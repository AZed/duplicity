"""Wrapper class around a file like "/usr/bin/env"

This class makes certain file operations more convenient and
associates stat information with filenames

"""

import stat, os, errno, pwd, grp, socket, time
import librsync
from lazy import *

_copy_blocksize = 64 * 1024
_tmp_path_counter = 1

class StatResult:
	"""Used to emulate the output of os.stat() and related"""
	# st_mode is required by the TarInfo class, but it's unclear how
	# to generate it from file permissions.
	st_mode = 0


class PathException(Exception): pass

class ROPath:
	"""Read only Path

	Objects of this class doesn't represent real files, so they don't
	have a name.  They are required to be indexed though.

	"""
	def __init__(self, index, stat = None):
		"""ROPath initializer"""
		self.opened, self.fileobj = None, None
		self.index = index
		self.stat, self.type = None, None
		self.mode, self.devnums = None, None

	def set_from_stat(self):
		"""Set the value of self.type, self.mode from self.stat"""
		if not self.stat: self.type = None

		st_mode = self.stat.st_mode
		if stat.S_ISREG(st_mode): self.type = "reg"
		elif stat.S_ISDIR(st_mode): self.type = "dir"
		elif stat.S_ISLNK(st_mode): self.type = "sym"
		elif stat.S_ISFIFO(st_mode): self.type = "fifo"
		elif stat.S_ISSOCK(st_mode): self.type = "sock"
		elif stat.S_ISCHR(st_mode): self.type = "chr"
		elif stat.S_ISBLK(st_mode): self.type = "blk"
		else: raise PathException("Unknown type")

		self.mode = stat.S_IMODE(st_mode)
		# The following can be replaced with major(), minor() macros
		# in later versions of python (>= 2.3 I think)
		self.devnums = (self.stat.st_rdev >> 8, self.stat.st_rdev & 0xff)
		
	def isreg(self):
		"""True if self corresponds to regular file"""
		return self.type == "reg"

	def isdir(self):
		"""True if self is dir"""
		return self.type == "dir"

	def issym(self):
		"""True if self is sym"""
		return self.type == "sym"

	def isfifo(self):
		"""True if self is fifo"""
		return self.type == "fifo"

	def issock(self):
		"""True is self is socket"""
		return self.type == "sock"

	def isdev(self):
		"""True is self is a device file"""
		return self.type == "chr" or self.type == "blk"

	def getdevloc(self):
		"""Return device number path resides on"""
		return self.stat.st_dev

	def open(self, mode):
		"""Return fileobj associated with self"""
		assert mode == "rb" and self.fileobj and not self.opened
		self.opened = 1
		return self.fileobj

	def setfileobj(self, fileobj):
		"""Set file object returned by open()"""
		assert not self.fileobj
		self.fileobj = fileobj
		self.opened = None

	def init_from_tarinfo(self, tarinfo):
		"""Set data from tarinfo object (part of tarfile module)"""
		# Set the typepp
		type = tarinfo.type
		if type == tarfile.REGTYPE or type == tarfile.AREGTYPE:
			self.type = "reg"
		elif type == tarfile.LNKTYPE:
			raise PathException("Hard links not supported yet")
		elif type == tarfile.SYMTYPE:
			self.type = "sym"
			self.symtext = tarinfo.linkname
		elif type == tarfile.CHRTYPE:
			self.type = "chr"
			self.devnums = (tarinfo.devmajor, tarinfo.devminor)
		elif type == tarfile.BLKTYPE:
			self.type = "blk"
			self.devnums = (tarinfo.devmajor, tarinfo.devminor)
		elif type == tarfile.DIRTYPE: self.type = "dir"
		elif type == tarfile.FIFOTYPE: self.type = "fifo"
		else: raise PathException("Unknown tarinfo type %s" % (type,))

		self.mode = tarinfo.mode
		self.stat = StatResult()

		# Set user and group id
		try: self.stat.st_uid = pwd.getpwnam(tarinfo.uname)[2]
		except KeyError:
			self.stat.st_uid = os.getuid() # default to current user
		try: self.stat.st_gid = grp.getgrnam(tarinfo.gname)[2]
		except KeyError:
			self.stat.st_gid = os.getgid() # default to current group

		self.stat.st_mtime = tarinfo.mtime
		self.stat.st_size = tarinfo.size

	def get_rorpath(self):
		"""Return rorpath copy of self"""
		new_rorpath = ROPath(self.index, self.stat)
		new_rorpath.type, new_rorpath.mode = self.type, self.mode
		if self.issym(): new_rorpath.symtext = self.symtext
		elif self.isdev(): new_rorpath.devnums = self.devnums
		return new_rorpath

	def get_tarinfo(self):
		"""Generate a tarfile.TarInfo object based on self

		Doesn't set size based on stat, because we may want to replace
		data wiht other stream.  Size should be set separately by
		calling function.

		"""
		ti = tarfile.TarInfo()
		if self.index: ti.name = "/".join(self.index)
		else: ti.name = "."
		if self.isdir(): ti.name += "/" # tar dir naming convention

		if self.type:
			# Lots of this is specific to tarfile.py, hope it doesn't
			# change much...
			if self.isreg(): ti.type = tarfile.REGTYPE
			elif self.isdir(): ti.type = tarfile.DIRTYPE
			elif self.isfifo(): ti.type = tarfile.FIFOTYPE
			elif self.issym():
				ti.type = tarfile.SYMTYPE
				ti.linkname = self.symtext
			elif self.isdev():
				if self.type == "chr": ti.type = tarfile.CHRTYPE
				else: ti.type = tarfile.BLKTYPE
				ti.devmajor, ti.devminor = self.devnums
			else: raise PathError("Unrecognized type " + str(self.type))

			ti.mode = self.mode
			ti.uid, ti.gid = self.stat.st_uid, self.stat.st_gid
			ti.mtime = self.stat.st_mtime

			try: ti.uname = pwd.getpwuid(ti.uid)[0]
			except KeyError: pass
			try: ti.gname = grp.getgrgid(ti.gid)[0]
			except KeyError: pass			

			if ti.type in (tarfile.CHRTYPE, tarfile.BLKTYPE):
				if hasattr(os, "major") and hasattr(os, "minor"):
					ti.devmajor = os.major(self.stat.st_rdev)
					ti.devminor = os.minor(self.stat.st_rdev)
		else:
			# Currently we depend on an uninitiliazed tarinfo file to
			# already have appropriate headers.  Still, might as well
			# make sure mode and size set.
			ti.mode, ti.size = 0, 0
		return ti

	def __eq__(self, other):
		"""Used to compare two ROPaths.  Doesn't look at fileobjs"""
		if not self.type and not other.type: return 1 # neither exists
		if not self.stat and other.stat or not other.stat and self.stat:
			return 0
		if self.type != other.type: return 0

		if self.isreg():
			# Don't compare sizes, because we would be comparing
			# signature size to size of file.
			return (self.perms_equal(other) and
					self.stat.st_mtime == other.stat.st_mtime)
		elif self.isdir() or self.isfifo(): return self.perms_equal(other)
		elif self.issym(): # here only symtext matters
			return self.symtext == other.symtext
		elif self.isdev():
			return self.perms_equal(other) and self.devnums == other.devnums
		assert 0

	def perms_equal(self, other):
		"""True if self and other have same permissions and ownership"""
		s1, s2 = self.stat, other.stat
		return (self.mode == other.mode and
				s1.st_gid == s2.st_gid and s1.st_uid == s2.st_uid)

	def copy(self, other):
		"""Copy self to other.  Also copies data.  Other must be Path"""
		if self.isreg(): other.writefileobj(self.open("rb"))
		elif self.isdir(): os.mkdir(other.name)
		elif self.issym():
			os.symlink(self.symtext, other.name)
			other.setdata()
			return # no need to copy symlink attributes
		elif self.isfifo(): os.mkfifo(other.name)
		elif self.issock(): socket.socket(socket.AF_UNIX).bind(other.name)
		elif self.isdev():
			if self.type == "chr": devtype = "c"
			else: devtype = "b"
			other.makedev("c", *self.devnums)
		self.copy_attribs(other)

	def copy_attribs(self, other):
		"""Only copy attributes from self to other"""
		if isinstance(other, Path):
			os.chown(other.name, self.stat.st_uid, self.stat.st_gid)
			os.chmod(other.name, self.mode)
			os.utime(other.name, (time.time(), self.stat.st_mtime))
			other.setdata()
		else: # write results to fake stat object
			assert isinstance(other, ROPath)
			stat = StatResult()
			stat.st_uid, stat.st_gid = self.stat.st_uid, self.stat.st_gid
			stat.st_mtime = self.stat.st_mtime
			other.stat = stat
			other.mode = self.mode


class Path(ROPath):
	def __init__(self, base, index = ()):
		"""Path initializer"""
		# self.opened should be true if the file has been opened, and
		# self.fileobj can override returned fileobj 
		self.opened, self.fileobj = None, None
		self.base = base
		self.index = index
		self.name = os.path.join(base, *index)
		self.setdata()

	def setdata(self):
		"""Refresh stat cache"""
		try: self.stat = os.lstat(self.name)
		except OSError, e:
			err_string = errno.errorcode[e[0]]
			if err_string == "ENOENT" or err_string == "ENOTDIR":
				self.stat, self.type = None, None # file doesn't exist
			else: raise
		else:
			self.set_from_stat()
			if self.issym(): self.symtext = os.readlink(self.name)

	def append(self, ext):
		"""Return new Path with ext added to index"""
		return self.__class__(self.base, self.index + (ext,))

	def new_index(self, index):
		"""Return new Path with index index"""
		return self.__class__(self.base, index)

	def listdir(self):
		"""Return list generated by os.listdir"""
		return os.listdir(self.name)

	def open(self, mode = "rb"):
		"""Return fileobj associated with self

		Usually this is just the file data on disk, but can be
		replaced with arbitrary data using the setfileobj method.

		"""
		assert not self.opened
		if self.fileobj: result = self.fileobj
		else: result = open(self.name, mode)
		return result

	def makedev(self, type, major, minor):
		"""Make a device file with specified type, major/minor nums"""
		cmdlist = ['mknod', self.name, type, str(major), str(minor)]
		if os.spawnvp(os.P_WAIT, 'mknod', cmdlist) != 0:
			raise PathException("Error running %s" % cmdlist)
		self.setdata()

	def mkdir(self):
		"""Make a directory at specified path"""
		os.mkdir(self.name)
		self.setdata()

	def delete(self):
		"""Remove this file"""
		log.Log("Deleting %s" % (self.name,), 7)
		if self.isdir(): os.rmdir(self.name)
		else: os.unlink(self.name)
		self.setdata()

	def deltree(self):
		"""Remove self by recursively deleting files under it"""
		log.Log("Deleting tree %s" % (self.name,), 7)
		itr = IterTreeReducer(PathDeleter, [])
		for path in selection.Select(self).set_iter(): itr(path.index, path)
		itr.Finish()
		self.setdata()

	def get_parent_dir(self):
		"""Return directory that self is in"""
		if self.index: return Path(self.base, self.index[:-1])
		else:
			components = self.base.split("/")
			if len(components) == 2 and not components[0]:
				return Path("/") # already in root directory
			else: return Path("/".join(components[:-1]))

	def writefileobj(self, fin):
		"""Copy file object fin to self.  Close both when done."""
		fout = self.open("wb")
		while 1:
			buf = fin.read(_copy_blocksize)
			if not buf: break
			fout.write(buf)
		if fin.close() or fout.close():
			raise PathException("Error closing file object")
		self.setdata()

	def rename(self, new_path):
		"""Rename file at current path to new_path.  Path stays same"""
		os.rename(self.name, new_path.name)
		self.setdata()
		new_path.setdata()

	def patch_with_attribs(self, diff_ropath):
		"""Patch self with diff and then copy attributes over"""
		assert self.isreg() and diff_ropath.isreg()
		temp_path = self.get_temp_in_same_dir()
		patch_fileobj = librsync.PatchedFile(self.open("rb"),
											 diff_ropath.open("rb"))
		temp_path.writefileobj(patch_fileobj)
		diff_ropath.copy_attribs(temp_path)
		temp_path.rename(self)

	def get_temp_in_same_dir(self):
		"""Return temp non existent path in same directory as self"""
		global _tmp_path_counter
		parent_dir = self.get_parent_dir()
		while 1:
			temp_path = parent_dir.append("duplicity_temp." +
										  str(_tmp_path_counter))
			if not temp_path.type: return temp_path
			_tmp_path_counter += 1
			assert _tmp_path_counter < 10000, \
				   "Warning too many temp files created for " + self.name

	def compare_recursive(self, other, verbose = None):
		"""Compare self to other Path, descending down directories"""
		selfsel = selection.Select(self).set_iter()
		othersel = selection.Select(other).set_iter()
		return Iter.equal(selfsel, othersel, verbose)

	def __str__(self):
		"""Return string representation"""
		return "(%s %s %s)" % (self.index, self.name, self.type)

class PathDeleter(ITRBranch):
	"""Delete a directory.  Called by Path.deltree"""
	def start_process(self, index, path): self.path = path
	def end_process(self): self.path.delete()
	def can_fast_process(self, index, path): return not path.isdir()
	def fast_process(self, index, path): path.delete()

	
# Wait until end to avoid circular module trouble
import robust, tarfile, log, selection
