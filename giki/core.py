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

        @param repo_path Path on disk to the Git repository the wiki is stored in.
        @param ref_name Ref name to consider the head of the wiki branch.
        """

        self._repo = Repo(repo_path)
        self._ref = ref_name

    def get_page(self, path):
        """Gets the page at a particular path.

        Subfolders should be specified with the `/` symbol, regardless of platform.

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
        """Gets the page at a particular path, at the commit with a particular sha.

        @return `WikiPage` object
        @raises PageNotFound if the page does not exist at that particular commit
        """
        p = WikiPage(self, path)
        p._load_from_commit(id)
        return p

    def create_page(self, path, fmt, author):
        p = WikiPage(self, path)
        p._create(fmt, author)
        return p

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
    commit_id = '' # The commit this page came from before modification
    _commit = None
    _orig_content = '' # For comparing to see if it's actually changed
    _trees = []
    _filename = '' #without extension

    def __init__(self, wiki, path):
        """Don't call this directly."""
        self.wiki = wiki
        self._repo = wiki._repo
        self.path = path
        self._trees = [] #tuples of (directory_name, tree_obj)

    def _create(self, fmt, author):
        self.commit_id = self._repo.ref(self.wiki._ref)
        self._commit = self._repo.commit(self.commit_id)
        self._walk_trees(True)

        try:
            self._find_blob()
        except PageNotFound:
            pass
        else:
            raise PageExists()

        self._orig_content = '!'
        self.content = "\n"
        self.fmt = fmt
        self.save(author.encode(self.wiki._encoding), 'Created {}'.format(self.path).encode(self.wiki._encoding))

    def _load(self):
        id = self._repo.ref(self.wiki._ref)
        self._load_from_commit(id)

    def _load_from_ref(self, ref):
        id = self._repo.ref(ref)
        self._load_from_commit(id)

    def _load_from_commit(self, commit_id):
        self.commit_id = commit_id
        self._commit = self._repo.commit(commit_id)
        self._walk_trees()
        blob = self._find_blob()


        self._orig_content = self.content = self._repo.object_store[blob.sha].as_raw_string().decode(self.wiki._encoding)

    def _walk_trees(self, create=False):
        """Populates `_trees` and `_filename`"""
        self._trees.append(('', self._repo.object_store[self._commit.tree]))

        if '/' in self.path:
            patharr = self.path.split('/')
            self._filename = patharr[-1]

            # loop through trees to find the immediate parent of our page
            tree = self._trees[0][1]
            for i in patharr[:-1]:
                i = i.encode(self.wiki._encoding)
                try:
                    tree_id = tree[i][1]
                except KeyError:
                    if create:
                        tree = Tree()
                        self._trees.append((i, tree))
                    else:
                        raise PageNotFound()
                else:
                    tree = self._repo.object_store[tree_id]
                    self._trees.append((i, tree))
        else:
            self._filename = self.path

    def _find_blob(self):
        # find a blob that matches our page's name, and discover its format
        try:
            tc = self._repo.object_store.iter_tree_contents(self._trees[-1][1].id)
            for i in tc:
                if i.path.startswith("{}.".format(self._filename)):
                    self.fmt = i.path.split(".")[1]
                    blob = i
                    break
            else:
                raise PageNotFound()
        except KeyError:
            raise PageNotFound()
        return blob

    def save(self, author, change_msg=''):
        """Saves a page to the respository.

        Makes a new commit with the modified contents of `content`, with `commit`
        as its parent commit. If `commit` is no longer the branch head, it may also
        add a separate merge commit.

        @param Author, in Git-style `name <email>` format.
        @param change_msg Commit message. Automatically generated if omitted/empty.
        @return id of the commit the modification was made in. Note that if a merge
            was performed, this may not be the branch head.
        """
        if self._orig_content == self.content:
            return self.commit

        if self.content[-1] != "\n":
            self.content += "\n"

        #save updated content to the tree
        blob = Blob.from_string(self.content.encode(self.wiki._encoding))
        full_filename = '.'.join((self._filename, self.fmt)).encode(self.wiki._encoding)

        immediate_parent_tree = self._trees[-1][1]

        immediate_parent_tree[full_filename] = (0100644, blob.id)

        self._repo.object_store.add_object(blob)
        self._repo.object_store.add_object(immediate_parent_tree)

        #loop backwards through parent trees
        for t in reversed(list(enumerate(self._trees[:-1]))):
            idx = t[0]
            tree = t[1][1]
            child_tree = self._trees[idx + 1]
            tree[child_tree[0]] = (040000, child_tree[1].id)
            self._repo.object_store.add_object(tree)

        #create a commit
        commit = Commit()
        commit.tree = self._trees[0][1].id
        commit.parents = [self.commit_id]
        commit.author = commit.committer = author.encode(self.wiki._encoding)
        commit.commit_time = commit.author_time = int(time())
        commit.commit_timezone = commit.author_timezone = 0
        commit.encoding = "UTF-8"
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
