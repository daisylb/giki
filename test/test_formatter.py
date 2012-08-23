"""Formatter tests.

These tests are not meant to be comprehensive tests of the external formatting libraries, but rather make sure that our wrapper code doesn't blow up.
"""

from giki.formatter import format

class DummyPage (object):
	def __init__(self, format, content):
		self.fmt = format
		self.content = content

def test_markdown():
	p = DummyPage('mdown', "# h1\n\nparagraph")
	assert '<h1>h1</h1>' in format(p)

def test_rst():
	p = DummyPage('rest', "h1\n==\n")
	assert '<h1 class="title">h1</h1>' in format(p)
	assert '<html' not in format(p)
	assert '<body' not in format(p)

def test_unknown():
	p = DummyPage('aoeuaoeu', "<>&")
	assert format(p) == "<code><pre>&lt;>&nbsp;</pre></code>"