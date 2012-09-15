from .web_framework import WebApp, get, post, Response, TemporaryRedirectResponse, NotFoundException
from .core import Wiki, PageNotFound
from .formatter import format, get_names
from jinja2 import Environment, PackageLoader
from StringIO import StringIO
from traceback import print_exc

t = Environment(loader=PackageLoader('giki', 'templates'))

class WebWiki (WebApp):
	def __init__(self, wiki):
		self.wiki = wiki
	
	def get_permission(self, request, type):
		"""Override this to implement permissions.
		
		@param type 'read' or 'write' as appropriate.
		@return the appropriate Git author string."""
		return 'Example Exampleson <example@example.com>'
	
	@get(r'^/$')
	def home(self, request):
		return TemporaryRedirectResponse('/index')
		
	@get(r'^/(?P<path>[^\+\.][^\.]+)')
	def show_page(self, request, path):
		self.get_permission(request, 'read')
		try:
			p = self.wiki.get_page(path)
		except PageNotFound:
			raise NotFoundException()
		fmt_human, fmt_cm = get_names(p)
		attrs = {
			'page': p,
			'content': format(p),
			'fmt_human': fmt_human,
			'fmt_cm': fmt_cm,
		}
		return Response(t.get_template('page.html').render(**attrs))
		
	@post(r'^/(?P<path>[^\+\.][^\.]+)')
	def save_page(self, request, path):
		author = self.get_permission(request, 'write')
		p = self.wiki.get_page_at_commit(path, request.vars.commit_id)
		p.content = request.vars.content
		p.save(author, request.vars.commit_msg)
		return self.show_page(request, path)
	
	@post(r'^/\+create$')
	def create_page(self, request):
		author = self.get_permission(request, 'write')
		p = self.wiki.create_page(request.vars.path, 'mdown', author)
		return TemporaryRedirectResponse('/' + request.vars.path)
	
	def handle_not_found(self, request, exc):
		return Response(t.get_template('404.html').render(request=request))
		
	def handle_internal_error(self, request, exc):
		io = StringIO()
		print_exc(file=io)
		return Response(t.get_template('500.html').render(request=request, traceback=io.getvalue()))

class SingleUserWiki (WebWiki):
	def __init__(self, wiki, author):
		WebWiki.__init__(self, wiki)
		self.author = author
	
	def get_permission(self, request, type):
		return self.author
	