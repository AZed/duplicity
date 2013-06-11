"""duplicity's gpg interface"""

import select, os, sys, thread
import GnuPGInterface

class GPGError(Exception):
	"""Indicate some GPG Error"""
	pass

class GPGFile:
	"""File-like object that encrypts or decrypts another file on the fly"""
	blocksize = 16 * 1024 # this was fastest on my system
	def __init__(self, encrypt, infp, passphrase):
		"""GPGFile initializer

		encrypt is 1 for encryption, 0 for decryption.  infp is a
		filelike object opened for reading.  passphrase is a string
		the passphrase is stored in.  Right now only symmetric
		encryption/decryption is supported.

		"""
		self.infp = infp
		self.buffer = ""
		self.at_end = None
		if encrypt: cmdlist = ['--symmetric']
		else: cmdlist = ['--decrypt']

		# Now start GPG process - copied from GnuPGInterface docstring.
		gnupg = GnuPGInterface.GnuPG()
		gnupg.options.meta_interactive = 0
		gnupg.options.extra_args.append('--no-secmem-warning')
		gnupg.passphrase = passphrase

		p1 = gnupg.run(cmdlist, create_fhs=['stdin', 'stdout'])
		self.gpg_process = p1
		self.gpg_input = p1.handles['stdin']
		self.gpg_output = p1.handles['stdout']

		thread.start_new_thread(self.feed_process, ())

	def read(self, length): return self.gpg_output.read(length)
	def close(self): return self.gpg_output.close()

	def feed_process(self):
		while 1:
			inbuf = self.infp.read(self.blocksize)
			if not inbuf: break
			self.gpg_input.write(inbuf)
		self.infp.close()
		self.gpg_input.close()

