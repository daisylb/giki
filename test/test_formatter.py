"""Formatter tests.

These tests are not meant to be comprehensive tests of the external formatting libraries, but rather make sure that our wrapper code doesn't blow up.
"""

from giki.formatter import format, get_names

class DummyPage (object):
	def __init__(self, format, content):
		self.fmt = format
		self.content = content

def test_markdown():
	p = DummyPage('mdown', "# h1\n\nparagraph")
	t = format(p)
	assert '<h1>h1</h1>' in t
	assert '<html' not in t
	assert '<body' not in t

def test_rst():
	p = DummyPage('rest', "h1\n==\n")
	t = format(p)
	assert '<h1 class="title">h1</h1>' in t
	assert '<html' not in t
	assert '<body' not in t

def test_textile():
	p = DummyPage('textile', "h1. test\n\n")
	t = format(p)
	print t
	assert '<h1>test</h1>' in t
	assert '<html' not in t
	assert '<body' not in t

def test_unknown():
	p = DummyPage('aoeuaoeu', "<>&")
	assert format(p) == "<code><pre>&lt;&gt;&nbsp;</pre></code>"

def test_names():
	p = DummyPage('mdown', "# h1\n\nparagraph")
	f, c = get_names(p)
	assert f == 'Markdown'
	assert c == 'markdown'

def test_names_unknown():
	p = DummyPage('aoeuaoeu', "# h1\n\nparagraph")
	f, c = get_names(p)
	assert f == 'aoeuaoeu'
	assert c is None
