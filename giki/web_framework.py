"""A really basic, object oriented web framework.

Why create our own? Because all of the other microframeworks I could find rely on things like module globals. This makes it difficult and untidy to create multiple instances of the same app, to do things like serve up different wikis."""

import re
from wsgiref.simple_server import make_server
from inspect import getmembers
from cgi import parse_qs, escape
from traceback import print_exc
import sys

class WebApp (object):
	"""Subclass this to create a web app."""
	
	__mounted_views = None
	debug = False
	
	def bind_view(self, path, verbs, view):
		"""Mount a view to a path."""
		if self.__mounted_views is None:
			self.__mounted_views = []
		self.__mounted_views.append((path, verbs, view))
	
	def handle_internal_error(self, request, exc):
		"""If a view raises an exception, then this handler is called. Override it to provide custom 500 handling.
		
		This handler is only called when an exception is raised. Views can return a 500 response *without* calling this handler by returning an ErrorResponse instance.
		
		Note that some specific exceptions are handled by other handlers. Instances of `Exception` are guaranteed to be handled by this method.
		
		@param request the Request object passed to the view.
		@param exc The exception that was raised.
		@return an ErrorResponse instance.
		"""
		if self.debug:
			print_exc(file=sys.stdout)
		return ErrorResponse("<html><body><h1>500 Internal Server Error</h1></body></html>")

	def handle_not_found(self, request, exc):
		"""If a view raises a NotFoundException, then this handler is called. Override it to provide custom 404 handling.
		
		This handler is only called when an NotFoundException is raised. Views can return a 404 response *without* calling this handler by returning a NotFoundResponse instance.
		
		This handler is also called if no view matches the given URL. In this case, `exc.no_view` will be `True`.
		
		@param request the Request object passed to the view.
		@param exc The exception that was raised.
		@return a NotFoundResponse instance.
		"""
		return NotFoundResponse("<html><body><h1>404 Not Found</h1></body></html>")
	
	def wsgi(self):
		"""Returns a WSGI app.
		
		This is not the callable itself, it *returns* the callable."""
		
		#Assemble views dictionary
		views = [(x[1].path, x[1].verbs, x[1]) for x in getmembers(self) if getattr(x[1], "_is_web_view", False)]
		if self.__mounted_views is not None:
			views += self.__mounted_views
				
		#compile regexes
		views = [(re.compile(a), b, c) for (a, b, c) in views]
		
		def app(environ, start_response):
			request = Request(environ)
			
			for path, verbs, view in views:
				if environ['REQUEST_METHOD'] not in verbs: continue
				match = path.match(environ['PATH_INFO'])
				if match is None: continue
				
				try:
					response = view(request, **match.groupdict())
					return response._do_response(start_response)
				except NotFoundException as exc:
					response = self.handle_not_found(request, exc)
					return response._do_response(start_response)
				except Exception as exc:
					response = self.handle_internal_error(request, exc)
					return response._do_response(start_response)
			else:
				# can't find an appropriate view
				exc = NotFoundException(no_view=True)
				response = self.handle_not_found(request, exc)
				return response._do_response(start_response)
		
		return app
		
	def serve(self, port):
		make_server('localhost', port, self.wsgi()).serve_forever()
		
		
#####
# REQUEST

class Request (object):
	def __init__(self, environ):
		self.environ = environ
	
	@property
	def method(self):
		return self.environ['REQUEST_METHOD']
	
	@property
	def host(self):
		return self.environ['HTTP_HOST']
	
	@property
	def path(self):
		return self.environ['PATH_INFO']
	
	@property
	def vars(self):
		if self.method == 'POST':
			request_body_size = int(self.environ.get('CONTENT_LENGTH', 0))
			request_body = self.environ['wsgi.input'].read(request_body_size)
			return Vars(request_body)
		else:
			return Vars(self.environ.get('QUERY_STRING', ''))

class Vars (object):
	def __init__(self, qs):
		self.environ_dict = parse_qs(qs)
	
	def __getattr__(self, attr):
		val = self.environ_dict.get(attr, None)
		if val is None:
			return None
		elif len(val) == 1:
			return val[0]
		else:
			return val
	
#####
# VIEW DECORATORS

"""These decorators just add a few attributes to instance methods, which are then picked up by `WebApp.wsgi`."""

class bind (object):
	"""Use this as a decorator to bind a view to a url"""
	def __init__(self, path, verbs):
		self.path = path
		self.verbs = verbs
	
	def __call__(self, func):
		func._is_web_view = True
		func.path = self.path
		func.verbs = self.verbs
		return func

class get (bind):
	def __init__(self, path):
		bind.__init__(self, path, ['GET'])

class post (bind):
	def __init__(self, path):
		bind.__init__(self, path, ['POST'])

#####
# RESPONSES

STATUS_STRINGS = {
	200: '200 OK',
	301: '301 Moved Permanently',
	302: '302 Found',
	403: '403 Forbidden',
	404: '404 Not Found',
	418: '418 I\'m a teapot',
	500: '500 Internal Server Error',
}

class Response (object):
	"""Represents a HTTP response.
	
	Return one of these from your views."""
	content = ""
	status = 200
	content_type = "text/html"
	headers = [] # the content type header is added later
	
	def __init__(self, content=None, status=None, content_type=None):
		self.headers = []
		if content is not None:
			self.content = content
		if status is not None:
			self.status = status
		if content_type is not None:
			self.content_type = content_type
	
	def add_header(self, header, value):
		self.headers.append((header, value))
	
	def _do_response(self, start_response):
		self.add_header('Content-Type', self.content_type)
		self.add_header('Content-Length', str(len(self.content)))
		start_response(STATUS_STRINGS.get(self.status, self.status), self.headers)
		return [self.content]

# Convenience response classes

class PermanentRedirectResponse (Response):
	status = 301
	def __init__(self, url, content=None, content_type=None):
		Response.__init__(self, content=content, content_type=content_type)
		self.add_header('Location', url)

class TemporaryRedirectResponse (PermanentRedirectResponse):
	status = 302

class ForbiddenResponse (Response):
	status = 403

class NotFoundResponse (Response):
	status = 404

class TeapotResponse (Response):
	status = 418

class ErrorResponse (Response):
	status = 500

#####
# Exceptions and Handlers

class NotFoundException (Exception):
	def __init__(self, no_view=False):
		self.no_view = no_view
