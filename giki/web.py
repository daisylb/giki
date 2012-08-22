from .web_framework import WebApp, get, post, Response
from .core import Wiki
from .formatter import format

class WebWiki (WebApp):
	def __init__(self, wiki):
		self.wiki = wiki
		
	@get('^/(?P<path>[^\.]+)')
	def show_page(self, request, path):
		p = wiki.get_page(path)
		return Response("<html><body>{}</body></html>".format(format(p)))

if __name__ == "__main__":
	from sys import argv
	wiki = Wiki(argv[1])
	app = WebWiki(wiki)
	app.serve(int(argv[2]))
	