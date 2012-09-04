from giki.web_framework import WebApp, bind, get, post, Response, NotFoundException, STATUS_STRINGS
from webtest import TestApp as TA

class _TestApp (WebApp):
	@bind(r'^/bind', ['GET', 'POST'])
	def test_bind(self, request):
		raise KeyError()
	
	@get(r'^/get')
	def test_get(self, request):
		return Response(content='abc')
	
	@get(r'^/404')
	def test_404(self, request):
		raise NotFoundException()
	
	@post(r'^/post')
	def test_post(self, request):
		pass

app = TA(_TestApp().wsgi())

def _dummy_req(path, method='GET'):
	return {
		'REQUEST_METHOD': method,
		'PATH_INFO': path
	}

def _noop(*args, **kwargs):
	pass

def test_bind_decorator():
	
	test_app = _TestApp()
	
	assert test_app.test_bind._is_web_view
	assert test_app.test_get._is_web_view
	assert test_app.test_post._is_web_view
	
	assert test_app.test_bind.path == r'^/bind'
	assert test_app.test_get.path == r'^/get'
	assert test_app.test_post.path == r'^/post'
	
	assert test_app.test_bind.verbs == ['GET', 'POST']
	assert test_app.test_get.verbs == ['GET']
	assert test_app.test_post.verbs == ['POST']

def test_routes():
	r = app.get('/get/banana')
	assert r.body == 'abc'

def test_routing_404():
	r = app.get('/eggs', status=404)
	assert r.status == STATUS_STRINGS[404]

def test_404():
	r = app.get('/404', status=404)
	assert r.status == STATUS_STRINGS[404]
	
def test_500():
	r = app.get('/bind', status=500)
	assert r.status == STATUS_STRINGS[500]