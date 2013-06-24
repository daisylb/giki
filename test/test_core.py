# coding: utf-8
from __future__ import unicode_literals
from . import setups
from nose import with_setup
from giki.core import Wiki, PageNotFound, PageExists

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_read():
    w = Wiki(setups.BARE_REPO_PATH)
    assert w.get_page('index').content == setups.EXAMPLE_TEXT

@with_setup(setups.setup_bare_with_two_branches, setups.teardown_bare)
def test_read_from_ref():
    w = Wiki(setups.BARE_REPO_PATH)
    assert w.get_page_at_branch('index', 'branch2').content == setups.EXAMPLE_TEXT_2

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_write():
    w = Wiki(setups.BARE_REPO_PATH)
    p = w.get_page('index')
    p.content = 'More Content\n'
    p.save(setups.EXAMPLE_AUTHOR, 'more stuff')
    assert w.get_page('index').content == 'More Content\n'

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_create():
    w = Wiki(setups.BARE_REPO_PATH)
    w.create_page('new', 'mdown', setups.EXAMPLE_AUTHOR)
    p = w.get_page('new')
    assert p.content == '\n'
    assert p.fmt == 'mdown'

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_read_subdir():
    w = Wiki(setups.BARE_REPO_PATH)
    assert w.get_page('test/test').content == setups.EXAMPLE_TEXT

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_write_subdir():
    w = Wiki(setups.BARE_REPO_PATH)
    p = w.get_page('test/test')
    p.content = 'More Content\n'
    p.save(setups.EXAMPLE_AUTHOR, 'more stuff')
    assert w.get_page('test/test').content == 'More Content\n'

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_create_in_subdir():
    w = Wiki(setups.BARE_REPO_PATH)
    w.create_page('test/test2', 'mdown', setups.EXAMPLE_AUTHOR)
    p = w.get_page('test/test2')
    assert p.content == '\n'
    assert p.fmt == 'mdown'

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_create_new_subdir():
    w = Wiki(setups.BARE_REPO_PATH)
    w.create_page('test2/test2', 'mdown', setups.EXAMPLE_AUTHOR)
    p = w.get_page('test2/test2')
    assert p.content == '\n'
    assert p.fmt == 'mdown'

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_nonexistent():
    w = Wiki(setups.BARE_REPO_PATH)
    try:
        w.get_page('aoeuaoeuaoeu')
    except PageNotFound:
        pass
    else:
        assert False

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_nonexistent_in_subdir():
    w = Wiki(setups.BARE_REPO_PATH)
    try:
        w.get_page('test/aoeuaoeuaoeuaoeuaoeu')
    except PageNotFound:
        pass
    else:
        assert False

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_nonexistent_subdir():
    w = Wiki(setups.BARE_REPO_PATH)
    try:
        w.get_page('aoeuaoeuaoeuaoeu/aoeuaoeuaoeuaoeuaoeu')
    except PageNotFound:
        pass
    else:
        assert False

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_create_existent():
    w = Wiki(setups.BARE_REPO_PATH)
    try:
        w.create_page('test/test', 'mdown', setups.EXAMPLE_AUTHOR)
    except PageExists:
        pass
    else:
        assert False

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_unicode_titles():
    w = Wiki(setups.BARE_REPO_PATH)
    w.create_page('いろはにほへとち/test', 'mdown', setups.EXAMPLE_AUTHOR)
    p = w.get_page('いろはにほへとち/test')

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_unicode_text():
    w = Wiki(setups.BARE_REPO_PATH)
    p = w.get_page('test/test')
    p.content = 'いろはにほへとち\n'
    p.save(setups.EXAMPLE_AUTHOR, 'unicode test')
    assert w.get_page('test/test').content == 'いろはにほへとち\n'

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_unicode_author():
    w = Wiki(setups.BARE_REPO_PATH)
    p = w.get_page('index')
    p.content = 'More Content\n'
    p.save('いろはにほへとち <unicode@author.com>', 'more stuff')
    # TODO: assert that author is in the history correctly

@with_setup(setups.setup_bare_with_page, setups.teardown_bare)
def test_merge_into_tree_with_modifications_to_different_files():
    w = Wiki(setups.BARE_REPO_PATH)
    w.create_page('test1', 'md', setups.EXAMPLE_AUTHOR)
    w.create_page('test2', 'md', setups.EXAMPLE_AUTHOR)
    p1 = w.get_page('test1')
    p2 = w.get_page('test2')
    p1.content = 'test1\n'
    p1.save(setups.EXAMPLE_AUTHOR)
    # the branch has now moved since p2 was pulled out of the repo
    p2.content = 'test2\n'
    p2.save(setups.EXAMPLE_AUTHOR) # this SHOULD commit our changes, then merge
                                   # in p1's changes
    p1 = w.get_page('test1') # re-pull from the current head
    print p1.content
    assert p1.content == 'test1\n'

# TODO: test that WikiPage.save() fails appropriately when the new commit's
# parent isn't an ancestor of the current commit (ie someone's rebased)
