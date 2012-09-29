from __future__ import unicode_literals
from docutils.core import publish_parts
from textile import textile
try:
	import misaka
except ImportError:
	from markdown2 import markdown

class __Formatter (object):
	def __init__(self):
		self.formats = []
		self.extensions = {}
	
	def type(self, format):
		self.formats.append(format)
		for ext in format.extensions:
			self.extensions[ext] = format
		return format
	
	def for_extension(self, ext):
		return self.extensions[ext]

formatter = __Formatter()

class __FormatType (object):
	pass

@formatter.type
class ReST (__FormatType):
	human_name = 'reStructuredText'
	codemirror_types = ('rst',)
	extensions = ('rst', 'rest')
	
	@staticmethod
	def format(string):
		"""Wraps the ReST parser in Docutils.
		
		Note that Docutils wraps its output in a `<div class='document'>`.
		"""
		return publish_parts(
			source=string,
			settings_overrides={
				'file_insertion_enabled': 0,
				'raw_enabled': 0,
				'--template': '%(body)s',
			},
			writer_name='html'
		)['html_body']

@formatter.type
class Markdown (__FormatType):
	human_name = 'Markdown'
	codemirror_types = ('markdown',)
	extensions = ('mdown', 'markdown', 'md', 'mdn', 'mkdn', 'mkd', 'mdn')
	
	@staticmethod
	def format(string):
		# Markdown uses Misaka if available, falling back to Markdown2
		if 'misaka' in globals():
			return misaka.html(string, extensions=
				misaka.EXT_STRIKETHROUGH |
				misaka.EXT_TABLES |
				misaka.EXT_FENCED_CODE |
				misaka.EXT_AUTOLINK |
				misaka.EXT_SUPERSCRIPT ,
				render_flags=misaka.HTML_SMARTYPANTS
			)
		else:
			return markdown(string, extras=[
				'fenced-code-blocks',
				'footnotes',
				'smarty-pants',
				'wiki-tables',
			])

@formatter.type
class Textile (__FormatType):
	human_name = 'Textile'
	codemirror_types = ()
	extensions = ('textile',)
	
	format = staticmethod(textile)

@formatter.type
class HTML (__FormatType):
	human_name = 'HTML'
	codemirror_types = ()
	extensions = ('html', 'htm')
	
	@staticmethod
	def format(string):
		return string
	

def format(page):
	"""Converts a giki page object into HTML.
	
	TODO: remove me and replace all calls to me
	TODO: implement some sort of post-processor interface for the table thing"""
	try:
		formatted_text = formatter.for_extension(page.fmt).format(page.content)
		return formatted_text.replace('<table>', '<table class="table">')
	except KeyError:
		return "<code><pre>{}</pre></code>".format(page.content.replace('&', '&nbsp;').replace('<', '&lt;').replace('>', '&gt;'))

def get_names(page):
	try:
		fmt = formatter.for_extension(page.fmt)
		return fmt.human_name, fmt.codemirror_types[0]
	except KeyError:
		return page.fmt, None