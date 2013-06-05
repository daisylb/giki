"""A Werkzeug-based picoframework.

Web apps are wholly contained in a class, meaning that multiple instances of the same app can be created in the same process.
"""

from copy import copy
from inspect import getmembers

from werkzeug.wrappers import Request
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound

class WebApp (object):
	"""Subclass this to create a web app."""
	__url_map = None

	def __build_url_map(self):
		"""Build the URL routing map.
		
		This is called the first time the app recieves a request.
		"""
		l = []

		for name, view in getmembers(self):
			if getattr(view, "_is_web_view", False):
				args, kwargs = view._routing_args
				kwargs = copy(kwargs) # don't mess up other instances
				kwargs['endpoint'] = name
				l.append(Rule(*args, **kwargs))

		self.__url_map = Map(l)

	def __dispatch_request(self, request):
		"""Dispatch a single request, and return a Werkzeug response."""
		if self.__url_map is None:
			self.__build_url_map()

		adapter = self.__url_map.bind_to_environ(request.environ)
		try:
			endpoint, values = adapter.match()
			return getattr(self, endpoint)(request, **values)
		except NotFound as e:
			return self.handle_not_found(request)
		except HTTPException, e:
			return e

	def wsgi_app(self, environ, start_response):
		"""The actual WSGI app callable."""
		request = Request(environ)
		response = self.__dispatch_request(request)
		return response(environ, start_response)

	def __call__(self, environ, start_response):
		"""This provides a shortcut so an instance of this class can be used as a WSGI app directly."""
		return self.wsgi_app(environ, start_response)

	def serve(self, port=8080):
		from werkzeug.serving import run_simple
		run_simple('127.0.0.1', port, self, use_debugger=self.debug, use_reloader=self.debug)
		
	
#####
# VIEW DECORATORS

class bind (object):
	"""Decorator to bind a view to a URL.
	
	Arguments are exactly the same as werkzeug.routing.Rule.
	"""

	def __init__(self, *args, **kwargs):
		self.r_args = args
		self.r_kwargs = kwargs
	
	def __call__(self, func):
		func._is_web_view = True
		func._routing_args = (self.r_args, self.r_kwargs)
		return func

class get (bind):
	def __init__(self, *args, **kwargs):
		super(get, self).__init__(*args, **kwargs)
		self.r_kwargs['methods'] = ['GET']

class post (bind):
	def __init__(self, *args, **kwargs):
		super(post, self).__init__(*args, **kwargs)
		self.r_kwargs['methods'] = ['POST']
