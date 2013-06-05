from .core import PageNotFound
from .formatter import format, get_names
from jinja2 import Environment, PackageLoader
from StringIO import StringIO
from traceback import print_exc

from werkzeug.wrappers import Response
from werkzeug.utils import redirect
from werkzeug.exceptions import NotFound

from .web_framework import WebApp, get, post, bind

t = Environment(loader=PackageLoader('giki', 'templates'))

class WebWiki (WebApp):
	debug = False

	def __init__(self, wiki):
		self.wiki = wiki

	# Authentication stuff

	def get_permission(self, request, kind):
		"""Override this to implement permissions.

		@param kind 'read' or 'write' as appropriate.
		@return the appropriate Git author string."""
		return 'Example Exampleson <example@example.com>'

	# Actual application stuff

	@get('/')
	def home(self, request):
		return redirect('/index')

	@bind('/<path:path>')
	def show_page(self, request, path):
		if request.method == 'GET':
			self.get_permission(request, 'read')
			try:
				p = self.wiki.get_page(path)
			except PageNotFound:
				raise NotFound()
			fmt_human, fmt_cm = get_names(p)

			# get path components for breadcrumb
			split_path = path.split('/')
			path_components = []
			if path != self.wiki.default_page:
				for i, cpt in enumerate(split_path):
					out_cpt = {
					'name': cpt,
					'path': '/'.join(split_path[:i])
					}
					path_components.append(out_cpt)

			attrs = {
				'page': p,
				'content': format(p),
				'fmt_human': fmt_human,
				'fmt_cm': fmt_cm,
				'path_components': path_components,
				'default_page': self.wiki.default_page,
			}
			return Response(t.get_template('page.html').render(**attrs), mimetype='text/html')
		elif request.method == 'POST':
			author = self.get_permission(request, 'write')
			p = self.wiki.get_page_at_commit(path, request.form['commit_id'])
			p.content = request.form['content']
			p.save(author, request.form['commit_msg'])
			return redirect('/' + path)

	def __repr__(self):
		return super(WebWiki, self).__repr__()

	@post('/+create')
	def create_page(self, request):
		author = self.get_permission(request, 'write')
		p = self.wiki.create_page(request.form['path'], 'mdown', author)
		return redirect('/' + request.form['path'])

	def handle_not_found(self, request):
		r = Response(t.get_template('404.html').render(request=request), mimetype='text/html')
		r.status_code = 404
		return r

	def handle_internal_error(self, request, exc):
		io = StringIO()
		print_exc(file=io)
		return Response(t.get_template('500.html').render(request=request, traceback=io.getvalue()))

class SingleUserWiki (WebWiki):
	def __init__(self, wiki, author):
		WebWiki.__init__(self, wiki)
		self.author = author

	def get_permission(self, request, kind):
		return self.author
