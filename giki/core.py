from dulwich.repo import Repo
from dulwich.objects import Blob, Commit
from time import time

class Wiki (object):
	"""Represents a Giki wiki."""

	_repo = None # Dulwich repo
	_ref = '' # the ref name to use

	def __init__(self, repo_path, ref_name="refs/heads/master"):
		"""Sets up the object.

		@param repo_path Path on disk to the Git repository the wiki is stored in.
		@param ref_name Ref name to consider the head of the wiki branch.
		"""

		self._repo = Repo(repo_path)
		self._ref = ref_name

	def _get_tree_for_page(self, root_tree, path, create=False):
		"""Returns (pagename, tree)"""
		if '/' in path:
			patharr = path.split('/')
			filename = patharr[-1]
			tree = root_tree
			# loop through trees to find the immediate parent of our page
			for i in patharr[:-1]:
				treeobj = self._repo.object_store[tree]
				tree = treeobj[i][1]
		else:
			filename = path
			tree = root_tree

		return filename, tree


	def _get_blob_for_page(self, commit, path):
		"""Returns (filetype, blob_sha)"""
		filename, tree = self._get_tree_for_page(commit.tree, path)

		# find a matching file in that tree
		for i in self._repo.object_store.iter_tree_contents(tree):
			if i.path.startswith("{}.".format(filename)):
				return i.path.split(".")[1], i.sha

		return None, None


	def get_page(self, path):
		"""Gets the page at a particular path.

		Subfolders should be specified with the `/` symbol, regardless of platform.

		@return `WikiPage` object
		"""
		# get the sha of the latest commit
		sha = self._repo.ref(self._ref)
		return self.get_page_at_commit(path, sha)

	def create_page(self, path, fmt, author):
		#get current tree
		old_commit_sha = self._repo.ref(self._ref)
		tree_sha = self._repo.commit(old_commit_sha).tree
		tree = self._repo.object_store[tree_sha]

		#save updated content to the tree
		blob = Blob.from_string('\n')
		filepath = '.'.join((path, fmt))
		tree[filepath] = (0100644, blob.id)

		#create a commit
		commit = Commit()
		commit.tree = tree.id
		commit.parents = [old_commit_sha]
		commit.author = commit.committer = author
		commit.commit_time = commit.author_time = int(time())
		commit.commit_timezone = commit.author_timezone = 0
		commit.encoding = "UTF-8"
		commit.message = "Create page {} with format {}".format(path, fmt)

		#write
		self._repo.object_store.add_object(blob)
		self._repo.object_store.add_object(tree)
		self._repo.object_store.add_object(commit)

		#update refs, to hell with concurrency (for now)
		self._repo.refs[self._ref] = commit.id


	def get_page_at_commit(self, path, sha):
		"""Gets the page at a particular path, at the commit with a particular sha.

		If you can't hold on to a page in memory while the user is editing it (eg
		in a web app), you should keep track of its `commit` and use this to store.

		@return `WikiPage` object
		"""
		commit = self._repo.commit(sha)
		page_fmt, page_sha1 = self._get_blob_for_page(commit, path)
		page_content = self._repo.object_store[page_sha1].as_raw_string()
		return WikiPage(self, sha, page_fmt, path, page_content)

	def _store_page(self, page, author, change_msg):
		if page._orig_content == page.content:
			return page.commit

		if page.content[-1] != "\n":
			page.content += "\n"

		#get tree that this edit was based on
		tree_sha = self._repo.commit(page.commit).tree
		tree = self._repo.object_store[tree_sha]

		#save updated content to the tree
		blob = Blob.from_string(page.content)
		filepath = '.'.join((page.path, page.fmt))
		tree[filepath] = (0100644, blob.id)

		#create a commit
		commit = Commit()
		commit.tree = tree.id
		commit.parents = [page.commit]
		commit.author = commit.committer = author
		commit.commit_time = commit.author_time = int(time())
		commit.commit_timezone = commit.author_timezone = 0
		commit.encoding = "UTF-8"
		commit.message = change_msg

		#write
		self._repo.object_store.add_object(blob)
		self._repo.object_store.add_object(tree)
		self._repo.object_store.add_object(commit)

		#update refs, to hell with concurrency (for now)
		self._repo.refs[self._ref] = commit.id


class WikiPage (object):
	"""Represents a page in a Giki wiki.

	Attributes are as follows:

	- `content` - the content of the page.
	- `fmt` - the file extension, eg `mdown` for Markdown.
	- `path` - the path to the page, not including extension.
	- `commit` - the sha of the commit this page came from.

	To edit the page, alter `content` and call `store()`. Don't touch the other
	attributes (yet).

	If you're giving the user this to edit later, be sure to give them the
	`commit` attribute, so you can find the same `WikiPage` to apply their
	edits to using `get_page_from_commit`.

	"""

	wiki = None
	content = ''
	fmt = ''
	path = ''
	commit = '' # The commit this page came from before modification
	_orig_content = '' # For comparing to see if it's actually changed

	def __init__(self, wiki, commit, fmt, path, content):
		"""Don't call this directly."""
		self.wiki = wiki
		self.commit = commit
		self.fmt = fmt
		self.path = path
		self._orig_content = self.content = content

	def store(self, author, change_msg=''):
		"""Saves a page to the respository.

		Makes a new commit with the modified contents of `content`, with `commit`
		as its parent commit. If `commit` is no longer the branch head, it may also
		add a separate merge commit.

		@param Author, in Git-style `name <email>` format.
		@param change_msg Commit message. Automatically generated if omitted/empty.
		@return sha of the commit the modification was made in. Note that if a merge
			was performed, this may not be the branch head.
		"""
		return self.wiki._store_page(self, author, change_msg)

class ManualMergeRequired (Exception):
	"""Raised if Giki cannot merge a change in automatically.

	If you recieve this exception, the changes have been safely committed to the
	repo (although they won't be attatched to anything, so you won't see them in
	a repo browsing tool, and they might get garbage collected if you leave them
	too long).

	TODO: what to do
	"""
	pass
