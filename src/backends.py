"""Provides functions and classes for getting/sending files to destination"""

import os
import log

class BackendException(Exception): pass

def get_backend(url_string):
	"""Return Backend object from url string

	url strings are like
	scp://foobar:password@hostname.net:124/usr/local.  If a protocol
	is unsupported an error will be returned.

	"""
	global protocol_class_dict
	def bad_url(message = None):
		if message:
			err_string = "Bad URL string '%s': %s" % (url_string, message)
		else: err_string = "Bad URL string '%s'" % url_string
		err_string += ("\nExample URL strings are file:///usr/local and "
					   "scp://root@host.net/dir\n"
					   "See the man page for more information")
		log.FatalError(err_string)

	colon_position = url_string.find(":")
	if colon_position < 1: bad_url()
	protocol = url_string[:colon_position]
	if url_string[colon_position+1:colon_position+3] != '//': bad_url()
	remaining_string = url_string[colon_position+3:]
	
	try: backend, separate_host = protocol_class_dict[protocol]
	except KeyError: bad_url("Unknown protocol '%s'" % protocol)
	assert not separate_host, "This part isn't done yet"

	return backend(remaining_string)


class Backend:
	"""Represent a connection to the destination device/computer

	This class only needs to have three methods: put(), and get(),
	which each take filenames, and list(), which should list the files
	available to get().

	"""
	def init(self, some_arguments): pass
	def put(self, pathname): pass
	def get(self, filename, dest_dir): pass
	def list(self): pass

	def run_command(self, commandline):
		"""Run given commandline with logging and error detection"""
		log.Log("Running '%s'" % commandline, 4)
		if os.system(commandline):
			raise BackendException("Error running '%s'" % commandline)

	def get_dir_filename(self, pathname):
		"""Return (parent_dir, filename) pair from pathname"""
		components = pathname.split("/")
		return ("/".join(components[:-1]), components[-1])

class LocalBackend(Backend):
	"""Use this backend when saving to local disk"""
	def __init__(self, target_dir):
		self.target_dir = target_dir

	def copyfileobj(infp, outfp):
		"""Copy file object infp to outfp, closing afterwards"""
		blocksize = 32 * 1024
		while 1:
			buf = infp.read(blocksize)
			if not buf: break
			outfp.write(buf)
		infp.close()
		outfp.close()

	def put(self, pathname):
		"""Try to rename first, copying if that doesn't work"""
		source_dir, filename = self.get_dir_filename(pathname)
		dest_path = os.path.join(self.target_dir, filename)
		log.Log("Writing %s" % dest_path, 4)
		try: os.rename(pathname, dest_path)
		except OSError: # rename failed, try copying
			self.copyfileobj(open(pathname, "rb"), open(dest_path, "wb"))

	def get(self, filename, dest_dir):
		"""Get file and put in dest_dir"""
		source_path = os.path.join(self.target_dir, filename)
		dest_path = os.path.join(dest_dir, filename)
		self.copyfileobj(open(source_path, "rb"), open(dest_path, "wb"))

	def list(self):
		"""List files in that directory"""
		return os.listdir(self.target_dir)

class scpBackend(Backend):
	"""This backend copies files using scp.  List not supported"""
	def __init__(self, url_string):
		"""scpBackend initializer

		Here url_string is something like
		username@host.net/file/whatever, which is produced after the 
		'scp://' of a url is stripped.

		"""
		self.scp_string = url_string.replace("/", ":", 1)

	def put(self, pathname):
		"""Use scp to copy source_dir/filename to remote computer"""
		filename = self.get_dir_filename(pathname)[1]
		commandline = "scp %s %s/%s" % (pathname, self.scp_string, filename)
		self.run_command(commandline)

	def get(self, filename, dest_dir):
		"""Use scp to get a remote file"""
		dest_path = Path(os.path.join(dest_dir, filename))
		commandline = "scp %s/%s %s" % (self.scp_string, filename,
										dest_path.name)
		self.run_command(commandline)
		dest_path.setdata()
		if not dest_path.exists():
			raise BackendException("File %s not found" % dest_path.name)
		
	def list(self):
		"""List files available for scp"""
		assert 0, "How do I list files for scp???"


# Dictionary relating protocol strings to tuples (backend_object,
# separate_host).  If separate_host is true, get_backend() above will
# parse the url futher to try to extract a hostname, protocol, etc.
protocol_class_dict = {"scp": (scpBackend, 0),
					   "file": (LocalBackend, 0)}
