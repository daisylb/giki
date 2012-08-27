from .web_framework import WebApp, get, post, Response, TemporaryRedirectResponse, NotFoundException
from .core import Wiki, PageNotFound
from .formatter import format

TEMPLATE = """
<!doctype html>
<html>
	<head>
		<title>{page.path}</title>
	</head>
	<body>
		<p><code>{page.commit_id}</code></p>
		{content}
		<form method=post>
			<textarea name=content>{page.content}</textarea>
			<button type=submit>Save</button>
			<input type=hidden name=id value="{page.commit_id}">
		</form>
	</body>
</html>
"""

class WebWiki (WebApp):
	def __init__(self, wiki):
		self.wiki = wiki
	
	@get('^/$')
	def home(self, request):
		return TemporaryRedirectResponse('/index')
		
	@get('^/(?P<path>[^\+\.][^\.]+)')
	def show_page(self, request, path):
		try:
			p = wiki.get_page(path)
		except PageNotFound:
			raise NotFoundException()
		attrs = {
			'page': p,
			'content': format(p),
		}
		return Response(TEMPLATE.format(**attrs))
		
	@post('^/(?P<path>[^\+\.][^\.]+)')
	def save_page(self, request, path):
		p = wiki.get_page_at_commit(path, request.vars.commit)
		p.content = request.vars.content
		p.save('Example Exampleson <example@example.com>', 'Example Commit')
		return self.show_page(request, path)

if __name__ == "__main__":
	from sys import argv
	wiki = Wiki(argv[1])
	app = WebWiki(wiki)
	app.debug = True
	app.serve(int(argv[2]))
	