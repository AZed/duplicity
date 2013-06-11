#!/usr/bin/env python

import sys, os, getopt
from distutils.core import setup, Extension

version_string = "0.0.0"

if sys.version_info[:2] < (2,2):
	print "Sorry, duplicity requires version 2.2 or later of python"
	sys.exit(1)

setup(name="duplicity",
	  version=version_string,
	  description="Untrusted backup using rsync algorithm",
	  author="Ben Escoto",
	  author_email="bescoto@stanford.edu",
	  url="http://rdiff-backup.stanford.edu/duplicity",
	  packages = ['duplicity'],
	  ext_modules = [Extension("duplicity._librsync",
							   ["_librsyncmodule.c"],
							   libraries=["rsync"])],
	  scripts = ['rdiffdir'],
	  data_files = [('share/man/man1', ['rdiffdir.1']),
					('share/doc/duplicity-%s' % version_string,
					 ['COPYING', 'README'])])




