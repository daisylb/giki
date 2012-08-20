from giki.web_framework import WebApp, bind, get, post

class TestApp (WebApp):
	@bind(r'^/bind', ['GET', 'POST'])
	def test_bind(self):
		pass
	
	@get(r'^/get')
	def test_get(self):
		pass
	
	@post(r'^/post')
	def test_post(self):
		pass

def test_bind_decorator():
	
	test_app = TestApp()
	
	assert test_app.test_bind._is_web_view
	assert test_app.test_get._is_web_view
	assert test_app.test_post._is_web_view
	
	assert test_app.test_bind.path == r'^/bind'
	assert test_app.test_get.path == r'^/get'
	assert test_app.test_post.path == r'^/post'
	
	assert test_app.test_bind.verbs == ['GET', 'POST']
	assert test_app.test_get.verbs == ['GET']
	assert test_app.test_post.verbs == ['POST']