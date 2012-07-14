from dulwich.repo import Repo
from dulwich.objects import Commit

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

	def _get_file_from_commit(self, commit, path):
		tree = self._repo.object_store[commit.tree]
		for i in self._repo.object_store.iter_tree_contents(tree):
			if i.path.starts_with("{}.".format(path)):
				return i.path.split(".")[1], self._repo.object_store[i.sha]


	def get_page(self, path):
		"""Gets the page at a particular path.

		@return `WikiPage` object
		"""
		latest_sha1 = self._repo.ref(self._ref)
		latest = self._repo.commit(latest_sha1)
		page_fmt, page_sha1 = self._get_file_from_commit(latest, path)
		page_content = self._repo.object_store[page_sha1].as_raw_string()
		return WikiPage(self, latest_sha1, page_fmt, path, page_content)

	def get_page_from_commit(self, commit, path):
		"""Gets the page from a certain location, as it was on a certain commit.

		If you can't hold on to a page in memory while the user is editing it (eg
		in a web app), you should
		"""

	def _store_page(self, page, author, change_msg):
		if (page._orig_content == page.content
		and page._orig_fmt == page.fmt
		and page._orig_path == page.path):
			return


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
		wiki._store_page(self, author, change_msg)
