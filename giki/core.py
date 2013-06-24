from __future__ import unicode_literals
from dulwich.repo import Repo
from dulwich.objects import Blob, Commit, Tree
from time import time

class Wiki (object):
    """Represents a Giki wiki."""

    _repo = None # Dulwich repo
    _ref = '' # the ref name to use
    _encoding = 'utf-8'
    default_page = 'index'

    def __init__(self, repo_path, ref_name="refs/heads/master"):
        """Sets up the object.

        @param repo_path Path on disk to the Git repository the wiki is in.
        @param ref_name Ref name to consider the head of the wiki branch.
        """

        self._repo = Repo(repo_path)
        self._ref = ref_name

    def get_page(self, path):
        """Gets the page at a particular path.

        Subfolders should be specified with the `/` symbol, not os.path.sep.

        @return `WikiPage` object
        @raises PageNotFound if the page does not exist
        """
        p = WikiPage(self, path)
        p._load()
        return p

    def get_page_at_branch(self, path, branch_name):
        p = WikiPage(self, path)
        p._load_from_ref("refs/heads/{}".format(branch_name))
        return p

    def get_page_at_commit(self, path, id):
        """Gets the page at a given path, at the commit with a given sha.

        @return `WikiPage` object
        @raises PageNotFound if the page does not exist at that commit
        """
        p = WikiPage(self, path)
        p._load_from_commit(id)
        return p

    def create_page(self, path, fmt, author):
        p = WikiPage(self, path)
        p._create(fmt, author)
        return p

    def __get_trees(self, root_tree, path, create=False):
        """Gets a list of trees specified by `path` relatve to `root_tree`.

        Returns a list of tuples in the form (name, tree_obj).
        """
        # accept either a string or tree object for the root tree
        if type(root_tree) in (str, unicode):
            root_tree = self._repo.object_store[root_tree]
            
        trees = [['', root_tree]]
        
        if len(path) == 0:
            return trees

        # loop through trees to find the immediate parent of our page
        tree = root_tree
        for i in path:
            i = i.encode(self._encoding)
            try:
                tree_type, tree_id = tree[i]
            except KeyError:
                if create:
                    tree = Tree()
                    trees.append([i, tree])
                else:
                    raise
            else:
                if tree_type != 040000:
                    raise KeyError()
                tree = self._repo.object_store[tree_id]
                trees.append([i, tree])

        return trees

    def _get_subtree(self, root_tree, path, create=False):
        """Returns a tree object for the subtree given by `path` relative to
        `root_tree`.
        """
        trees = self.__get_trees(root_tree, path, create=create)
        return trees[-1][1]

    def _put_subtree(self, root_tree, path, new_tree):
        """Replaces the subtree at `path` relative to `root_tree` with
        `new_tree`, then returns the new root tree object.
        """
        trees = self.__get_trees(root_tree, path, create=True)

        # insert our new subtree into the list
        trees[-1][1] = new_tree
        self._repo.object_store.add_object(new_tree)

        # update all the parent trees
        for i, (_, tree) in reversed(list(enumerate(trees[:-1]))):
            child_name, child_tree = trees[i+1]
            tree[child_name] = (040000, child_tree.id)
            self._repo.object_store.add_object(tree)

        # return the root tree
        return trees[0][1]


class WikiPage (object):
    """Represents a page in a Giki wiki.

    Attributes are as follows:

    - `content` - the content of the page.
    - `fmt` - the file extension, eg `mdown` for Markdown.
    - `path` - the path to the page, not including extension.
    - `commit_id` - the id of the commit this page came from.

    To edit the page, alter `content` and call `store()`. Don't touch the other
    attributes (yet).

    If you're giving the user this to edit later, be sure to give them the
    `commit_id` attribute, so you can find the same `WikiPage` to apply their
    edits to using `get_page_from_commit`.
    """

    wiki = None
    content = ''
    fmt = ''
    path = ''
    _path_list = None
    _name = ''
    commit_id = '' # The commit this page came from before modification
    _commit = None
    _orig_content = '' # For comparing to see if it's actually changed

    def __init__(self, wiki, path):
        """Don't call this directly."""
        self.wiki = wiki
        self._repo = wiki._repo
        self.path = path
        self._path_list = path.split('/')
        self._name = self._path_list[-1]

    def _create(self, fmt, author):
        self.commit_id = self._repo.ref(self.wiki._ref)
        self._commit = self._repo.commit(self.commit_id)

        try:
            self._find_blob()
        except PageNotFound:
            pass
        else:
            raise PageExists()

        self._orig_content = '!'
        self.content = "\n"
        self.fmt = fmt
        self.save(author.encode(self.wiki._encoding),
                'Created {}'.format(self.path).encode(self.wiki._encoding))

    def _load(self):
        id = self._repo.ref(self.wiki._ref)
        self._load_from_commit(id)

    def _load_from_ref(self, ref):
        id = self._repo.ref(ref)
        self._load_from_commit(id)

    def _load_from_commit(self, commit_id):
        self.commit_id = commit_id
        self._commit = self._repo.commit(commit_id)
        blob = self._find_blob()

        self.content = blob.as_raw_string().decode(self.wiki._encoding)
        self._orig_content = self.content

    def _find_blob(self):
        # find a blob that matches our page's name, and discover its format
        try:
            subtree = self.wiki._get_subtree(self._commit.tree,
                    self._path_list[:-1])
            
            for mode, name, sha in subtree.entries():
                # if it's not a regular or executable file, keep going
                if mode not in (0100644, 0100755):
                    continue

                # test the name
                if name.startswith("{}.".format(self._name)):
                    self.fmt = name.split(".")[1]
                    return self._repo.object_store[sha]
        except KeyError:
            raise PageNotFound()

        # if we get to here, we haven't found it
        raise PageNotFound()

    def save(self, author, change_msg=''):
        """Saves a page to the respository.

        Makes a new commit with the modified contents of `content`, with
        `commit` as its parent commit. If `commit` is no longer the branch head,
        it may also add a separate merge commit.

        @param Author, in Git-style `name <email>` format.
        @param change_msg Commit message. Automatically generated if
        omitted/empty.
        @return id of the commit the modification was made in. Note that if a
        merge was performed, this may not be the branch head.
        """
        # Don't write a redundant commit if the content is the same.
        if self._orig_content == self.content:
            return self.commit_id

        # Ensure there's a trailing newline.
        if self.content[-1] != "\n":
            self.content += "\n"

        # save updated content to the tree
        blob = Blob.from_string(self.content.encode(self.wiki._encoding))
        self._repo.object_store.add_object(blob)

        # grab the tree we're replacing
        full_filename = '.'.join((self._name, self.fmt)).encode(
                self.wiki._encoding)
        new_tree = self.wiki._get_subtree(self._commit.tree,
                self._path_list[:-1], create=True)

        # grab the old blob ID (which we'll use later)
        try:
            _, old_blob_id = new_tree[full_filename]
        except KeyError:
            new_file = True

        # insert the new tree into the tree, and save
        new_tree[full_filename] = (0100644, blob.id)
        new_root_tree = self.wiki._put_subtree(self._commit.tree,
                self._path_list[:-1], new_tree)

        # create a commit
        commit = Commit()
        commit.tree = new_root_tree.id
        commit.parents = [self.commit_id]
        commit.author = commit.committer = author.encode(self.wiki._encoding)
        commit.commit_time = commit.author_time = int(time())
        commit.commit_timezone = commit.author_timezone = 0
        commit.encoding = self.wiki._encoding
        commit.message = change_msg
        self._repo.object_store.add_object(commit)

        #update refs, to hell with concurrency (for now)
        self._repo.refs[self.wiki._ref] = commit.id

class PageNotFound (Exception):
    pass

class PageExists (Exception):
    pass

class ManualMergeRequired (Exception):
    """Raised if Giki cannot merge a change in automatically.

    If you recieve this exception, the changes have been safely committed to the
    repo (although they won't be attatched to anything, so you won't see them in
    a repo browsing tool, and they might get garbage collected if you leave them
    too long).

    TODO: what to do
    """
    pass
