"""Log various messages depending on verbosity level"""

import sys

verbosity = 3
termverbosity = 3

def Log(s, verb_level):
	"""Write s to stderr if verbosity level low enough"""
	if verb_level <= termverbosity: sys.stderr.write(s + "\n")

def FatalError(s):
	"""Write fatal error message and exit"""
	sys.stderr.write(s + "\n")
	sys.exit(1)

def setverbosity(verb, termverb = None):
	"""Set the verbosity level"""
	global verbosity, termverbosity
	verbosity = verb
	if termverb: termverbosity = termverb
	else: termverbosity = verb
