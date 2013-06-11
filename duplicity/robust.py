import librsync, errno, log

def check_common_error(error_handler, function, args = []):
	"""Apply function to args, if error, run error_handler on exception

	This only catches certain exceptions which seem innocent
	enough.

	"""
	try: return function(*args)
	#except (EnvironmentError, SkipFileException, DSRPPermError,
	#		RPathException, Rdiff.RdiffException,
	#		librsync.librsyncError, C.UnknownFileTypeError), exc:
	#	TracebackArchive.add()
	except (EnvironmentError, librsync.librsyncError), exc:
		if (not isinstance(exc, EnvironmentError) or
			(errno.errorcode[exc[0]] in
			 ['EPERM', 'ENOENT', 'EACCES', 'EBUSY', 'EEXIST',
			  'ENOTDIR', 'ENAMETOOLONG', 'EINTR', 'ENOTEMPTY',
			  'EIO', 'ETXTBSY', 'ESRCH', 'EINVAL'])):
			#Log.exception()
			if error_handler: return error_handler(exc, *args)
		else:
			#Log.exception(1, 2)
			raise

def listpath(path):
	"""Like path.listdir() but return [] if error, and sort results"""
	def error_handler(exc):
		log.Log("Error listing directory %s" % rp.path, 2)
		return []
	dir_listing = check_common_error(error_handler, path.listdir)
	dir_listing.sort()
	return dir_listing
