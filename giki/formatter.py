from markdown2 import markdown

# A tuple containing all supported formats.
# Each line goes (format name, tuple of possible file extensions, formatter)
# where formatter is a callable that takes a string and returns a HTML string
PAGE_FORMATS = (
	('Markdown', ('mdown', 'markdown', 'md', 'mdn', 'mkdn', 'mkd', 'mdn'), markdown),
)

def format(page):
	"""Converts a giki page object into HTML."""
	for name, fmts, formatter in PAGE_FORMATS:
		if page.fmt in fmts:
			return formatter(page.content)
		else:
			return page.content