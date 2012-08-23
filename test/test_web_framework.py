from giki.web_framework import WebApp, bind, get, post, Response, NotFoundException, STATUS_STRINGS

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
	test_app = _TestApp()
	
	environ = _dummy_req('/get/banana')
		
	assert test_app.wsgi()(environ, _noop) == ['abc']

def test_routing_404():
	test_app = _TestApp()
	
	environ = _dummy_req('/eggs')
	
	response_run = [False]
	
	def start_response(status, headers):
		assert status == STATUS_STRINGS[404]
		response_run[0] = True
		
	test_app.wsgi()(environ, start_response)
	
	assert response_run[0]

def test_404():
	test_app = _TestApp()
	
	environ = _dummy_req('/eggs')
	
	response_run = [False]
	
	def start_response(status, headers):
		assert status == STATUS_STRINGS[404]
		response_run[0] = True
		
	test_app.wsgi()(environ, start_response)
	
	assert response_run[0]
	
def test_500():
	test_app = _TestApp()
	
	environ = _dummy_req('/bind')
	
	response_run = [False]
	
	def start_response(status, headers):
		assert status == STATUS_STRINGS[500]
		response_run[0] = True
		print 'yay'
		
	test_app.wsgi()(environ, start_response)
	
	assert response_run[0]