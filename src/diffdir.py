"""Functions for signatures, deltas, and patching of directories"""

from __future__ import generators
import cStringIO, re
import tarfile, librsync, log
from path import *
from lazy import *

# Deltas will be broken up into volume_size chunks, so that an entire
# delta doesn't have to be read into memory.
volume_size = 1024 * 1024

class DiffDirException(Exception): pass


####################################################################
#
# DirSig section - make multifile signatures
#

def DirSig(path_iter):
	"""Return tarfileobj containing signatures of paths in given path_iter"""
	def make_pair_iter(path_iter):
		"""Produce (tarinfo, fileobj) sig iterator from path iterator"""
		for path in path_iter:
			ti = path.get_tarinfo()
			if path.isreg():
				# Must put size into tarinfo first, so read sig into memory
				sfp = librsync.SigFile(path.open("rb"))
				sigbuf = sfp.read()
				sfp.close()
				ti.size = len(sigbuf)
				yield (ti, cStringIO.StringIO(sigbuf))
			else: yield (ti, None)
	return tarfile.TarFromIterator(make_pair_iter(path_iter))

def Tar_WriteSig(path_iter, sig_outfp):
	"""Return normal tar file object, write signatures too

	Like in DirDelta_WriteSig below, the signature tarfile written to
	sig_outfp will be over the same data contained in the tarfile.

	"""
	sigTarFile = tarfile.TarFile("none", "w", sig_outfp)
	def callback(sig_string, path):
		"""This is run when FileWithSignature is read to end"""
		ti = path.get_tarinfo()
		ti.size = len(sig_string)
		sigTarFile.addfile(ti, cStringIO.StringIO(sig_string))

	def get_pair(path):
		"""Return ti, fileobj pair from path"""
		ti = path.get_tarinfo()
		if path.isreg():
			fws = FileWithSignature(path.open("rb"), callback, path)
			return (ti, fws)
		else:
			sigTarFile.addfile(ti)
			return (ti, None)

	def error_handler(exc, path):
		"""This is called when there is a problem in get_pair()"""
		log.Log("Skipping %s because of error: %s" % (path.name, str(exc)), 2)
		return None

	def make_pair_iter(path_iter):
		"""Produce (tarinfo, fileobj) iterator from path_iter"""
		for path in path_iter:
			result = robust.check_common_error(error_handler, get_pair,
											   (path,))
			if result is not None: yield result
		sigTarFile.close()
	return tarfile.TarFromIterator(make_pair_iter(path_iter))

def Tar(path_iter):
	"""Return normal tarfile.  Just provided for completeness (no diffing)"""
	def make_pair_iter():
		for path in path_iter:
			ti = path.get_tarinfo()
			if path.isreg(): yield (ti, path.open("rb"))
			else: yield (ti, None)
	return tarfile.TarFromIterator(make_pair_iter())


####################################################################
#
# DirDelta section - make multifile deltas
#

def DirDelta(path_iter, dirsig_fileobj):
	"""Produce tarfileobj diff given tarfile dirsig_fileobj and pathiter"""
	delta_iter = get_delta_iter(path_iter, tar2path_iter(dirsig_fileobj))
	return tarfile.TarFromIterator(delta_iter2tar_iter(delta_iter))

def delta_iter2tar_iter(delta_iter):
	"""Generate (tarinfo, fileobj) pairs from delta_iter

	Separates out deleted, snapshot, and diff files like:

	deleted/foo
	snapshot/usr/local
	etc

	"""
	for delta_ropath in delta_iter:
		if delta_ropath.fileobj:
			if delta_ropath.difftype == "diff":
				for ti, fileobj in delta_ropath2tar_iter(delta_ropath):
					yield (ti, fileobj)
				continue

			ti = delta_ropath.get_tarinfo()
			if delta_ropath.difftype == "snapshot":
				ti.size = delta_ropath.stat.st_size
				fileobj = delta_ropath.open("rb")
			else: fileobj = None
		else:
			ti = delta_ropath.get_tarinfo()
			fileobj = None

		if not delta_ropath.type: ti.name = "deleted/" + ti.name
		else: ti.name = "snapshot/" + ti.name
		yield (ti, fileobj)

def delta_ropath2tar_iter(delta_ropath):
	"""Turn delta_ropath into (possibly multivol) (tarinfo, fileobj) iter"""
	# See if one volume is sufficient
	fp = delta_ropath.open("rb")
	buf = fp.read(volume_size)
	if len(buf) < volume_size:
		fp.close()
		ti = delta_ropath.get_tarinfo()
		ti.name = "diff/" + ti.name
		ti.size = len(buf)
		yield (ti, cStringIO.StringIO(buf))
		return

	# Nope, we need multiple volumes
	volume_number = 1
	while len(buf) == volume_size:
		yield get_multivol_diff(delta_ropath, fp, buf, volume_number)
		buf = fp.read(volume_size)
		volume_number += 1
	yield get_multivol_diff(delta_ropath, fp, buf, volume_number)

def get_multivol_diff(delta_ropath, fileobj, buf, vol_num):
	"""Return one volume of multivol diff from delta_ropath and buf"""
	ti = delta_ropath.get_tarinfo()
	ti.name = "multivol_diff/%s/%d" % (ti.name, vol_num)
	ti.size = len(buf)
	return (ti, cStringIO.StringIO(buf))

def delta_iter_error_handler(exc, new_path, sig_path, sig_tar = None):
	"""Called by get_delta_iter, report error in getting delta"""
	if new_path: index_string = new_path.get_relative_path()
	elif sig_path: index_string = sig_path.get_relative_path()
	else: assert 0, "Both new and sig are None for some reason"
	log.Log("Error %s getting delta for %s" % (str(exc), index_string), 2)
	return None

def get_delta_path(new_path, sig_path):
	"""Get one delta_path, or None if error"""
	delta_path = new_path.get_rorpath()
	if not new_path.isreg():
		delta_path.difftype = "snapshot"
	elif not sig_path or not sig_path.isreg():
		delta_path.difftype = "snapshot"
		delta_path.setfileobj(new_path.open("rb"))
	else: # both new and sig exist and are regular files
		delta_path.difftype = "diff"
		sigfp, newfp = sig_path.open("rb"), new_path.open("rb")
		delta_path.setfileobj(librsync.DeltaFile(sigfp, newfp))
	new_path.copy_attribs(delta_path)
	delta_path.stat.st_size = new_path.stat.st_size		
	return delta_path

def get_delta_iter(new_iter, sig_iter):
	"""Generate delta iter from new Path iter and sig Path iter.

	For each delta path of regular file type, path.difftype with be
	set to "snapshot", "diff".  sig_iter will probably iterate ROPaths
	instead of Paths.

	"""
	collated = collate_iters(new_iter, sig_iter)
	for new_path, sig_path in collated:
		log.Log("Comparing %s and %s" % (new_path and new_path.index,
										 sig_path and sig_path.index), 6)
		if not new_path or not new_path.type:
			yield ROPath(sig_path.index) # indicates deleted
		elif sig_path and new_path == sig_path: pass # no change, skip
		else:
			delta_path = robust.check_common_error(delta_iter_error_handler,
												   get_delta_path,
												   (new_path, sig_path))
			if delta_path: yield delta_path # otherwise error

def tar2path_iter(tarobj):
	"""Given tar file object open for reading, yield contained paths"""
	tf = tarfile.TarFile("Arbitrary Name", "r", tarobj)
	tf.debug = 2
	for tarinfo in tf:
		if tarinfo.name == "./" or tarinfo.name == ".": index = ()
		else:
			index = tuple(tarinfo.name.split("/"))
			if not index[-1]: index = index[:-1] # deal with trailing /
		ropath = ROPath(index)
		ropath.init_from_tarinfo(tarinfo)
		if ropath.isreg(): ropath.setfileobj(tf.extractfile(tarinfo))
		yield ropath
	tarobj.close()

def collate_iters(riter1, riter2):
	"""Collate two iterators.

	The elements yielded by each iterator must be have an index
	variable, and this function returns pairs (elem1, elem2), (elem1,
	None), or (None, elem2) two elements in a pair will have the same
	index, and earlier indicies are yielded later than later indicies.

	"""
	relem1, relem2 = None, None
	while 1:
		if not relem1:
			try: relem1 = riter1.next()
			except StopIteration:
				if relem2: yield (None, relem2)
				for relem2 in riter2: yield (None, relem2)
				break
			index1 = relem1.index
		if not relem2:
			try: relem2 = riter2.next()
			except StopIteration:
				if relem1: yield (relem1, None)
				for relem1 in riter1: yield (relem1, None)
				break
			index2 = relem2.index

		if index1 < index2:
			yield (relem1, None)
			relem1 = None
		elif index1 == index2:
			yield (relem1, relem2)
			relem1, relem2 = None, None
		else: # index2 is less
			yield (None, relem2)
			relem2 = None


def DirDelta_WriteSig(path_iter, oldsig_infp, newsig_outfp):
	"""Like DirDelta but also write signature into sig_fileobj"""
	sig_path_iter = tar2path_iter(oldsig_infp)
	delta_iter = get_delta_iter_w_sig(path_iter, sig_path_iter, newsig_outfp)
	return tarfile.TarFromIterator(delta_iter2tar_iter(delta_iter))

def get_delta_iter_w_sig(path_iter, sig_path_iter, sig_fileobj):
	"""Like get_delta_iter but also write signatures to sig_fileobj"""
	collated = collate_iters(path_iter, sig_path_iter)
	sigTarFile = tarfile.TarFile("arbitrary", "w", sig_fileobj)
	for new_path, sig_path in collated:
		log.Log("Comparing %s and %s" % (new_path and new_path.index,
										 sig_path and sig_path.index), 6)
		if not new_path or not new_path.type: # file deleted
			yield ROPath(sig_path.index)
		elif sig_path and new_path == sig_path:
			# Same, just write old sig information, no delta output
			ti = sig_path.get_tarinfo()
			if sig_path.fileobj:
				sigfp = sig_path.open("rb")
				sigbuf = sigfp.read()
				sigfp.close()
				ti.size = len(sigbuf)
				sigTarFile.addfile(ti, cStringIO.StringIO(sigbuf))
			else: sigTarFile.addfile(ti)
		else: # Must calculate new signature and create delta
			delta_path = robust.check_common_error(
				delta_iter_error_handler, get_delta_path_w_sig,
				(new_path, sig_path, sigTarFile))
			if delta_path: yield delta_path
	sigTarFile.close()

def get_delta_path_w_sig(new_path, sig_path, sigTarFile):
	"""Return new delta_path which, when read, writes sig to sig_fileobj"""
	assert new_path
	ti = new_path.get_tarinfo()
	delta_path = new_path.get_rorpath()

	def callback(sig_string):
		"""Callback activated when FileWithSignature read to end"""
		ti.size = len(sig_string)
		sigTarFile.addfile(ti, cStringIO.StringIO(sig_string))

	if not new_path.isreg():
		delta_path.difftype = "snapshot"
		sigTarFile.addfile(ti)
	elif not sig_path or not sig_path.isreg():
		delta_path.difftype = "snapshot"
		delta_path.setfileobj(FileWithSignature(new_path.open("rb"),
												callback))
	else: # both are regular files
		delta_path.difftype = "diff"
		old_sigfp = sig_path.open("rb")
		newfp = FileWithSignature(new_path.open("rb"), callback)
		delta_path.setfileobj(librsync.DeltaFile(old_sigfp, newfp))
	new_path.copy_attribs(delta_path)
	delta_path.stat.st_size = new_path.stat.st_size
	return delta_path


class FileWithSignature:
	"""File-like object which also computes signature as it is read"""
	blocksize = 32 * 1024
	def __init__(self, infile, callback, *extra_args):
		"""FileTee initializer

		The object will act like infile, but whenever it is read it
		add infile's data to a SigGenerator object.  When the file has
		been read to the end the callback will be called with the
		calculated signature, and any extra_args if given.

		"""
		self.infile, self.callback = infile, callback
		self.sig_gen = librsync.SigGenerator()
		self.activated_callback = None
		self.extra_args = extra_args

	def read(self, length = -1):
		buf = self.infile.read(length)
		self.sig_gen.update(buf)
		return buf

	def close(self):
		# Make sure all of infile read
		if not self.activated_callback:
			while self.read(self.blocksize): pass
			self.activated_callback = 1
			self.callback(self.sig_gen.getsig(), *self.extra_args)
		return self.infile.close()
	

####################################################################
#
# DirPatch section - use deltas to patch directories
#

def DirPatch(base_path, difftarobj):
	"""Patch given Path object using delta tar fileobj difftarobj"""
	path_iter = selection.Select(base_path).set_iter()
	collated = collate_iters(path_iter, difftar2path_iter(difftarobj))
	ITR = IterTreeReducer(PathPatcher, [base_path])
	for basis_path, diff_ropath in collated:
		if basis_path: index = basis_path.index
		else: index = diff_ropath.index
		ITR(index, basis_path, diff_ropath)
	ITR.Finish()

def difftar2path_iter(difftarobj):
	"""Turn file-like difftarobj into iterator of ROPaths"""
	prefixes = ["snapshot/", "diff/", "deleted/"]
	tf = tarfile.TarFile("arbitrary", "r", difftarobj)
	tar_iter = iter(tf)
	tarinfo_list = [tar_iter.next()] # StopIteration will be passed upwards
	multivol_fileobj = None
	while 1:
		# This is used when a multivol diff is last in tar
		if not tarinfo_list[0]: raise StopIteration
		if multivol_fileobj and not multivol_fileobj.at_end:
			mulitvol_fileobj.close() # aborting in middle of multivol
			continue
		
		index, difftype, multivol = get_index_from_tarinfo(tarinfo_list[0])
		ropath = ROPath(index)
		ropath.init_from_tarinfo(tarinfo_list[0])
		ropath.difftype = difftype
		if ropath.isreg():
			if multivol:
				multivol_fileobj = Multivol_Filelike(tf, tar_iter,
													 tarinfo_list, index)
				ropath.setfileobj(multivol_fileobj)
				yield ropath
				continue # Multivol_Filelike will reset tarinfo_list
			else:
				ropath.setfileobj(tf.extractfile(tarinfo_list[0]))
		yield ropath
		tarinfo_list[0] = tar_iter.next()

def get_index_from_tarinfo(tarinfo):
	"""Return (index, difftype, multivol) pair from tarinfo object"""
	for prefix in ["snapshot/", "diff/", "multivol_diff/", "deleted/"]:
		if tarinfo.name.startswith(prefix):
			name = tarinfo.name[len(prefix):] # strip prefix
			if prefix == "multivol_diff/":
				difftype = "diff"
				multivol = 1
				name, num_subs = re.subn("^multivol_diff/(.*)/[0-9]+$",
										 "\\1", tarinfo.name)
				if num_subs != 1:
					raise DiffDirException("Unrecognized diff entry %s" %
										   (tarinfo.name,))
			else:
				difftype = prefix[:-1] # strip trailing /
				name = tarinfo.name[len(prefix):]
				if name.endswith("/"): name = name[:-1] # strip trailing /'s
				multivol = 0
			break
	else: raise DiffDirException("Unrecognized diff entry %s" %
								 (tarinfo.name,))
	if name == ".": index = ()
	else: index = tuple(name.split("/"))
	return (index, difftype, multivol)


class Multivol_Filelike:
	"""Emulate a file like object from multivols

	Maintains a buffer about the size of a volume.  When it is read()
	to the end, pull in more volumes as desired.

	"""
	def __init__(self, tf, tar_iter, tarinfo_list, index):
		"""Initializer.  tf is TarFile obj, tarinfo is first tarinfo"""
		self.tf, self.tar_iter = tf, tar_iter
		self.tarinfo_list = tarinfo_list # must store as list for write access
		self.index = index
		self.buffer = ""
		self.at_end = 0

	def read(self, length = -1):
		"""Read length bytes from file"""
		if length < 0:
			while self.addtobuffer(): pass
			real_len = len(self.buffer)
		else:
			while len(self.buffer) < length:
				if not self.addtobuffer(): break
			real_len = min(len(self.buffer), length)

		result = self.buffer[:real_len]
		self.buffer = self.buffer[real_len:]
		return result

	def addtobuffer(self):
		"""Add next chunk to buffer"""
		if self.at_end: return None
		index, difftype, multivol = get_index_from_tarinfo(
			self.tarinfo_list[0])
		if not multivol or index != self.index: # we've moved on
			# the following communicates next tarinfo to difftar2path_iter
			self.at_end = 1
			return None

		fp = self.tf.extractfile(self.tarinfo_list[0])
		self.buffer += fp.read()
		fp.close()

		try: self.tarinfo_list[0] = self.tar_iter.next()
		except StopIteration:
			self.tarinfo_list[0] = None
			self.at_end = 1
			return None
		return 1

	def close(self):
		"""If not at end, read remaining data"""
		if not self.at_end:
			while 1:
				self.buffer = ""
				if not self.addtobuffer(): break
		self.at_end = 1
		

class PathPatcher(ITRBranch):
	"""Used by DirPatch, process the given basis and diff"""
	def __init__(self, base_path):
		"""Set base_path, Path of root of tree"""
		self.base_path = base_path
		self.dir_diff_ropath = None

	def start_process(self, index, basis_path, diff_ropath):
		"""Start processing when diff_ropath is a directory"""
		if not (diff_ropath and diff_ropath.isdir()):
			assert index == () # this should only happen for first elem
			self.fast_process(index, basis_path, diff_ropath)
			return
			
		if not basis_path:
			basis_path = self.base_path.new_index(index)
			basis_path.mkdir() # Need place for later files to go into
		elif not basis_path.isdir():
			basis_path.delete()
			basis_path.mkdir()
		self.dir_basis_path = basis_path
		self.dir_diff_ropath = diff_ropath

	def end_process(self):
		"""Copy directory permissions when leaving tree"""
		if self.dir_diff_ropath:
			self.dir_diff_ropath.copy_attribs(self.dir_basis_path)

	def can_fast_process(self, index, basis_path, diff_ropath):
		"""No need to recurse if diff_ropath isn't a directory"""
		return not (diff_ropath and diff_ropath.isdir())

	def fast_process(self, index, basis_path, diff_ropath):
		"""For use when neither is a directory"""
		if not diff_ropath: return # no change
		elif not basis_path:
			if diff_ropath.difftype == "deleted": pass # already deleted
			else:  # just copy snapshot over
				diff_ropath.copy(self.base_path.new_index(index))
		elif diff_ropath.difftype == "deleted":
			if basis_path.isdir(): basis_path.deltree()
			else: basis_path.delete()
		elif not basis_path.isreg():
			if basis_path.isdir(): basis_path.deltree()
			else: basis_path.delete()
			diff_ropath.copy(basis_path)
		else:
			assert diff_ropath.difftype == "diff", diff_ropath.difftype
			basis_path.patch_with_attribs(diff_ropath)
