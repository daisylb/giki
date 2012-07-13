from dulwich.repo import Repo

class Wiki (object):
	"""Represents a Giki wiki."""

	_repo = None # Dulwich repo

	def __init__(self, repo_path):
		"""Sets up the object.

		@param path Path to the Git repository the wiki is stored in.
		"""

		self._repo = Repo(path)

	def get_page(self, path):
		"""Gets the page at a particular location.

		@return `WikiPage` object
		"""

	def store_page(self, path, author, page, change_msg=''):
		"""Saves a page to the respository.

		@param path Path to the page.
		@param Author, in Git-style `name <email>` format.
		@param page your WikiPage object
		@param change_msg Commit message. Automatically generated if omitted/empty.
		"""

class WikiPage (object):
	"""Represents a page in a Giki wiki.

	Attributes you can read and modify are as follows:

	- `content` - the content of the page.
	- `fmt` - the file extension, eg `mdown` for Markdown.
	- `path` - the path to the page, not including extension.
	"""

	content = ''
	fmt = ''
	path = ''
	_orig_commit = '' # The commit this page came from before modification
	_orig_content = '' # For comparing to see if it's actually changed
	_orig_path = '' # in case the page gets moved
	_orig_fmt = '' # ...or the format gets changed
