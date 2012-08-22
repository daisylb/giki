from giki.web_framework import WebApp, bind, get, post, Response

class _TestApp (WebApp):
	@bind(r'^/bind', ['GET', 'POST'])
	def test_bind(self, request):
		pass
	
	@get(r'^/get')
	def test_get(self, request):
		return Response(content='abc')
	
	@post(r'^/post')
	def test_post(self, request):
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
	test_app = _TestApp()
	
	environ = {
		'REQUEST_METHOD': 'GET',
		'PATH_INFO': '/get/banana'
	}
		
	assert test_app.wsgi()(environ, lambda x, y: x) == ['abc']
	