"""duplicity's gpg interface"""

import select, os, sys, thread, sha
import GnuPGInterface, misc

blocksize = 16 * 1024

class GPGError(Exception):
	"""Indicate some GPG Error"""
	pass

class GPGFile:
	"""File-like object that decrypts another file on the fly"""
	def __init__(self, encrypt, encrypt_path, passphrase):
		"""GPGFile initializer

		encrypt_path is the Path of the gpg encrypted file.  Right now
		only symmetric encryption/decryption is supported.

		"""
		# Start GPG process - copied from GnuPGInterface docstring.
		gnupg = GnuPGInterface.GnuPG()
		gnupg.options.meta_interactive = 0
		gnupg.options.extra_args.append('--no-secmem-warning')
		gnupg.passphrase = passphrase
		if encrypt:
			p1 = gnupg.run(['--symmetric'], create_fhs=['stdin'],
						   attach_fhs={'stdout': encrypt_path.open("wb")})
			self.gpg_input = p1.handles['stdin']
		else:
			p1 = gnupg.run(['--decrypt'], create_fhs=['stdout'],
						   attach_fhs={'stdin': encrypt_path.open("rb")})
			self.gpg_output = p1.handles['stdout']
		self.gpg_process = p1
		self.encrypt = encrypt

		# Following left over from trying to manage both ends
		# self.gpg_input = p1.handles['stdin']
		# thread.start_new_thread(self.feed_process, ())

	def read(self, length = -1): return self.gpg_output.read(length)
	def write(self, buf): return self.gpg_input.write(buf)

	def close(self):
		if self.encrypt:
			self.gpg_input.close()
			self.gpg_process.wait()
		else:
			self.gpg_output.close()
			self.gpg_process.wait()

	def feed_process(self):
		while 1:
			inbuf = self.infp.read(blocksize)
			if not inbuf: break
			self.gpg_input.write(inbuf)
		self.infp.close()
		self.gpg_input.close()


def GPGWriteFile(block_iter, filename, passphrase,
				 size = 50 * 1024 * 1024, max_footer_size = 16 * 1024):
	"""Write GPG compressed file of given size

	This function writes a gpg compressed file by reading from the
	input iter and writing to filename.  When it has read an amount
	close to the size limit, it "tops off" the incoming data with
	incompressible data, to try to hit the limit exactly.

	block_iter should have methods .next(), which returns the next
	block of data, and .peek(), which returns the next block without
	deleting it.  Also .get_footer() returns a string to write at the
	end of the input file.  The footer should have max length
	max_footer_size.

	"""
	def start_gpg(filename, passphrase):
		"""Start GPG process, return (process, to_gpg_fileobj)"""
		gnupg = GnuPGInterface.GnuPG()
		gnupg.options.meta_interactive = 0
		gnupg.options.extra_args.append('--no-secmem-warning')
		gnupg.passphrase = passphrase

		p1 = gnupg.run(['--symmetric'], create_fhs=['stdin'],
					   attach_fhs={'stdout': open(filename, "wb")})
		return (p1, p1.handles['stdin'])

	def top_off(bytes, to_gpg_fp):
		"""Add bytes of incompressible data to to_gpg_fp

		In this case we take the incompressible data from the
		beginning of filename (it should contain enough because size
		>> largest block size).

		"""
		incompressible_fp = open(filename, "rb")
		assert misc.copyfileobj(incompressible_fp, to_gpg_fp, bytes) == bytes
		incompressible_fp.close()

	def get_current_size(): return os.stat(filename).st_size

	def close_process(gpg_process, to_gpg_fp):
		"""Close gpg process and clean up"""
		to_gpg_fp.close()
		gpg_process.wait()

	target_size = size - 18 * 1024 # fudge factor, compensate for gpg buffering
	check_size = target_size - max_footer_size
	gpg_process, to_gpg_fp = start_gpg(filename, passphrase)
	while (block_iter.peek() and
		   get_current_size() + len(block_iter.peek().data) <= check_size):
		to_gpg_fp.write(block_iter.next().data)
	to_gpg_fp.write(block_iter.get_footer())
	if block_iter.peek():
		cursize = get_current_size()
		if cursize < target_size: top_off(target_size - cursize, to_gpg_fp)
	close_process(gpg_process, to_gpg_fp)

		
def get_sha_hash(path, hex = 1):
	"""Return SHA1 hash of path, in hexadecimal form if hex is true"""
	assert path.isreg()
	blocksize = 64 * 1024
	fp = path.open("rb")
	sha_obj = sha.new()
	while 1:
		buf = fp.read(blocksize)
		if not buf: break
		sha_obj.update(buf)
	assert not fp.close()
	if hex: return sha_obj.hexdigest()
	else: return sha_obj.digest()
