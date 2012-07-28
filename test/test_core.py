from . import setups
from nose import with_setup
from giki.core import Wiki

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_read():
	w = Wiki(setups.BARE_REPO_PATH)
	assert w.get_page('index').content == setups.EXAMPLE_TEXT

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_write():
	w = Wiki(setups.BARE_REPO_PATH)
	p = w.get_page('index')
	p.content = 'More Content\n'
	p.store(setups.EXAMPLE_AUTHOR, 'more stuff')
	assert w.get_page('index').content == 'More Content\n'

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_create():
	w = Wiki(setups.BARE_REPO_PATH)
	w.create_page('index', 'mdown', setups.EXAMPLE_AUTHOR)
	p = w.get_page('index')
	assert p.content == '\n'
	assert p.fmt == 'mdown'
