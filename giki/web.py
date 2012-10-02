from .core import Wiki, PageNotFound
from .formatter import format, get_names
from jinja2 import Environment, PackageLoader
from StringIO import StringIO
from traceback import print_exc

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule

t = Environment(loader=PackageLoader('giki', 'templates'))

class WebWiki (object):
	debug = False
	
	def __init__(self, wiki):
		self.wiki = wiki
		
		# construct routing map
		self.url_map = Map([
			Rule('/', endpoint='home'),
			Rule('/<page>', endpoint='page'),
			Rule('/+create', endpoint='create'),
		])
	
	# WSGI stuff
	
	def wsgi_app(self, environ, start_response):
		request = Request(environ)
		response = self.dispatcher(request)
		return response(environ, start_response)
	
	def dispatcher(self, request):
		return Response('Hello World!')
	
	def __call__(self, environ, start_response):
		return self.wsgi_app(environ, start_response)
	
	def serve(self, port=8080):
		from werkzeug.serving import run_simple
		run_simple('127.0.0.1', port, self, use_debugger=self.debug, use_reloader=self.debug)
	
	# Authentication stuff
	
	def get_permission(self, request, type):
		"""Override this to implement permissions.
		
		@param type 'read' or 'write' as appropriate.
		@return the appropriate Git author string."""
		return 'Example Exampleson <example@example.com>'
	
	# Actual application stuff
	
	def home(self, request):
		return TemporaryRedirectResponse('/index')
		
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
		
	def save_page(self, request, path):
		author = self.get_permission(request, 'write')
		p = self.wiki.get_page_at_commit(path, request.vars.commit_id)
		p.content = request.vars.content.decode('utf8')
		p.save(author, request.vars.commit_msg)
		return self.show_page(request, path)
	
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
	