from markdown2 import markdown
from docutils.core import publish_parts
from textile import textile

def rst(string):
	"""Wraps the ReST parser in Docutils.
	
	Note that Docutils wraps its output in a `<div class='document'>`."""
	return publish_parts(
		source=string,
		settings_overrides={
			'file_insertion_enabled': 0,
			'raw_enabled': 0,
			'--template': '%(body)s',
		},
		writer_name='html'
	)['html_body']

def md(string):
	return markdown(string, extras=[
		'fenced-code-blocks',
		'footnotes',
		'smarty-pants',
		'wiki-tables',
	])

# A tuple containing all supported formats.
# Each line goes (format name, tuple of possible file extensions, formatter)
# where formatter is a callable that takes a string and returns a HTML string
PAGE_FORMATS = (
	('Markdown', 'markdown', ('mdown', 'markdown', 'md', 'mdn', 'mkdn', 'mkd', 'mdn'), md),
	('reStructuredText', 'rst', ('rst', 'rest'), rst),
	('Textile', None, ('textile'), textile),
	('HTML', None, ('html', 'htm'), lambda x: x),
)

def __get_pf(fmt):
	for i in PAGE_FORMATS:
		if fmt in i[2]:
			return i
	else:
		return None, None, None, None
	

def format(page):
	"""Converts a giki page object into HTML."""
	_, _, _, formatter = __get_pf(page.fmt)
	
	if formatter is not None:
		return formatter(page.content)
	else:
		return "<code><pre>{}</pre></code>".format(page.content.replace('&', '&nbsp;').replace('<', '&lt;'))

def get_names(page):
	friendly_name, codemirror_name, _, _ = __get_pf(page.fmt)
	if friendly_name is not None:
		return friendly_name, codemirror_name
	else:
		return page.fmt, None