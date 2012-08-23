from setuptools import setup
import os

setup(name='giki',
	version='0.1pre',
	description='a Git-based wiki',
	author='Adam Brenecki',
	author_email='adam@brenecki.id.au',
	url='',
	packages=['.'.join(i[0].split(os.sep))
		for i in os.walk('giki')
		if '__init__.py' in i[2]],
	install_requires=[
		'dulwich==0.8.5',
		# formatters
		'markdown2==2.0.1',
		'docutils==0.9.1',
		'textile==2.1.5',
	],
	entry_points={
    'console_scripts':
        ['giki = giki.cli:main'],
	},
)
