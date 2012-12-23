from subprocess import call
from shutil import rmtree
from dulwich.repo import Repo
from dulwich.objects import Blob, Commit, Tree
from time import time
from os import mkdir

EXAMPLE_TEXT = '# Example\nexample example example'
EXAMPLE_TEXT_2 = '# Example2\nexample example example'
EXAMPLE_AUTHOR = 'Test Testington <test@example.com>'
BARE_REPO_PATH = '_test_bare.git'

def setup_bare():
	mkdir(BARE_REPO_PATH)
	Repo.init_bare(BARE_REPO_PATH)

def setup_bare_with_page():
	setup_bare()
	r = Repo(BARE_REPO_PATH)
	b = Blob.from_string(EXAMPLE_TEXT)
	t = Tree()
	t.add('index.mdown', 0100644, b.id)
	t2 = Tree()
	t2.add('test.mdown', 0100644, b.id)
	t.add('test', 040000, t2.id)
	c = Commit()
	c.tree = t.id
	c.author = c.committer = EXAMPLE_AUTHOR
	c.commit_time = c.author_time = int(time())
	c.commit_timezone = c.author_timezone = 0
	c.encoding = "UTF-8"
	c.message = 'Initial Commit'
	r.refs['refs/heads/master'] = c.id

	#write
	r.object_store.add_object(b)
	r.object_store.add_object(t)
	r.object_store.add_object(t2)
	r.object_store.add_object(c)

def setup_bare_with_two_branches():
	setup_bare_with_page()
	r = Repo(BARE_REPO_PATH)
	b = Blob.from_string(EXAMPLE_TEXT_2)
	t = Tree()
	t.add('index.mdown', 0100644, b.id)
	t2 = Tree()
	t2.add('test.mdown', 0100644, b.id)
	t.add('test', 040000, t2.id)
	c = Commit()
	c.tree = t.id
	c.author = c.committer = EXAMPLE_AUTHOR
	c.commit_time = c.author_time = int(time())
	c.commit_timezone = c.author_timezone = 0
	c.encoding = "UTF-8"
	c.message = 'Second Commit'
	r.refs['refs/heads/branch2'] = c.id

	#write
	r.object_store.add_object(b)
	r.object_store.add_object(t)
	r.object_store.add_object(t2)
	r.object_store.add_object(c)

def teardown_bare():
	rmtree(BARE_REPO_PATH)
