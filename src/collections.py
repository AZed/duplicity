"""Classes and functions on collections of backup volumes"""

import gzip
import log, file_naming, path, dup_time, globals

class CollectionsError(Exception): pass

class BackupSet:
	"""Backup set - the backup information produced by one session"""
	def __init__(self, backend):
		"""Initialize new backup set, only backend is required at first"""
		self.backend = backend
		self.info_set = None
		self.volume_name_dict = {} # dict from volume number to filename
		self.remote_manifest_name = None
		self.local_manifest_path = None
		self.time = None # will be set if is full backup set
		self.start_time, self.end_time = None, None # will be set if inc

	def is_complete(self):
		"""Assume complete if found manifest file"""
		return self.remote_manifest_name

	def add_filename(self, filename):
		"""Add a filename to given set.  Return true if it fits.

		The filename will match the given set if it has the right
		times and is of the right type.  The information will be set
		from the first filename given.

		"""
		pr = file_naming.parse(filename)
		if not pr: return None

		if not self.info_set: self.set_info(pr)
		else:
			if pr.type != self.type: return None
			if pr.time != self.time: return None
			if (pr.start_time != self.start_time or
				pr.end_time != self.end_time): return None

		if pr.manifest: self.set_manifest(filename)
		else:
			assert pr.volume_number is not None
			assert not self.volume_name_dict.has_key(pr.volume_number), \
				   (self.volume_name_dict, filename)
			self.volume_name_dict[pr.volume_number] = filename
		return 1

	def set_info(self, pr):
		"""Set BackupSet information from ParseResults object"""
		assert not self.info_set
		self.type = pr.type
		self.time = pr.time
		self.start_time, self.end_time = pr.start_time, pr.end_time
		self.time = pr.time
		self.info_set = 1

	def set_manifest(self, remote_filename):
		"""Add local and remote manifest filenames to backup set"""
		assert not self.remote_manifest_name, (self.remote_manifest_name,
											   remote_filename)
		self.remote_manifest_name = remote_filename

		if not globals.archive_dir: return
		for local_filename in globals.archive_dir.listdir():
			pr = file_naming.parse(local_filename)
			if (pr and pr.manifest and pr.type == self.type and
				pr.time == self.time and pr.start_time == self.start_time
				and pr.end_time == self.end_time):
				self.local_manifest_path = \
							  globals.archive_dir.append(local_filename)
				break

	def delete(self):
		"""Remove all files in set"""
		self.backend.delete(self.remote_manfest_name)
		for filename in self.volume_name_dict: self.backend.delete(filename)

	def __str__(self):
		"""For now just list files in set"""
		filelist = []
		if self.remote_manifest_name:
			filelist.append(self.remote_manifest_name)
		filelist.extend(self.volume_name_dict.values())
		return "\n".join(filelist)

	def get_timestr(self):
		"""Return time string suitable for log statements"""
		return dup_time.timetopretty(self.time or self.end_time)


class BackupChain:
	"""BackupChain - a number of linked BackupSets

	A BackupChain always starts with a full backup set and continues
	with incremental ones.

	"""
	def __init__(self, backend):
		"""Initialize new chain, only backend is required at first"""
		self.backend = backend
		self.fullset = None
		self.incset_list = [] # sorted list of BackupSets
		self.start_time, self.end_time = None, None

	def set_full(self, fullset):
		"""Add full backup set"""
		assert not self.fullset and isinstance(fullset, BackupSet)
		self.fullset = fullset
		assert fullset.time
		self.start_time, self.end_time = fullset.time, fullset.time

	def add_inc(self, incset):
		"""Add incset to self.  Return None if incset does not match"""
		if self.end_time == incset.start_time:
			self.incset_list.append(incset)
			self.end_time = incset.end_time
			assert self.end_time
			return 1
		else: return None

	def delete(self):
		"""Delete all sets in chain, in reverse order"""
		for i in range(len(self.incset_list)-1, -1, -1):
			self.incset_list[i].delete()

	def get_sets_at_time(self, time):
		"""Return a list of sets in chain earlier or equal to time"""
		older_incsets = filter(lambda s: s.end_time <= time, self.incset_list)
		return [self.fullset] + older_incsets


class SignatureChain:
	"""A number of linked signatures

	Analog to BackupChain - start with a full-sig, and continue with
	new-sigs.

	"""
	def __init__(self, archive_dir):
		"""Return new SignatureChain.  archive_dir is Path sigs are in"""
		self.archive_dir = archive_dir
		self.fullsig = None
		self.inclist = []
		self.start_time, self.end_time = None, None

	def add_path(self, sigpath, pr = None):
		"""Add new signature path to current chain.  Return true if it fits"""
		if not pr: pr = file_naming.parse(sigpath.get_filename())
		if not pr: return None

		if self.fullsig:
			if pr.type != "new-sig": return None
			if pr.start_time != self.end_time: return None
			self.inclist.append(sigpath)
			self.end_time = pr.end_time
			return 1
		else:
			if pr.type != "full-sig": return None
			self.fullsig = sigpath
			self.start_time, self.end_time = pr.time, pr.time
			return 1
		
	def get_fileobjs(self):
		"""Return ordered list of signature fileobjs opened for reading"""
		assert self.fullsig
		return map(lambda sigpath: gzip.GzipFile(sigpath.name, "rb"),
				   [self.fullsig] + self.inclist)

	def delete(self):
		"""Remove all files in signature set"""
		for i in range(len(self.inclist)-1, -1, -1): self.inclist[i].delete()
		self.fullsig.delete()


class CollectionsStatus:
	"""Hold information about available chains and sets"""
	def __init__(self, backend, archive_dir):
		"""Make new object.  Does not set values"""
		self.backend = backend
		self.archive_dir = archive_dir

		# Will hold (signature chain, backup chain) pair of active
		# (most recent) chains
		self.matched_chain_pair = None

		# These should be sorted by end_time
		self.all_backup_chains = None
		self.other_backup_chains = None
		self.other_sig_chains = None

		# Other misc paths and sets which shouldn't be there
		self.orphaned_sig_paths = None
		self.orphaned_backup_sets = None
		self.incomplete_backup_sets = None

		# True if set_values() below has run
		self.values_set = None

	def set_values(self, backend_filename_list = None, no_archive_dir = None):
		"""Set values from archive_dir and backend.  Return self"""
		if backend_filename_list is None:
			backend_filename_list = self.backend.list()
		backup_chains, self.orphaned_backup_sets, self.incomplete_backup_set=\
					   self.get_backup_chains(backend_filename_list)
		backup_chains = self.get_sorted_chains(backup_chains)
		self.all_backup_chains = backup_chains
		if no_archive_dir: return self # only process backend

		sig_chains, self.orphaned_sig_paths = self.get_signature_chains()
		sig_chains = self.get_sorted_chains(sig_chains)

		if sig_chains and backup_chains:
			sig_chain, backup_chain = sig_chains[-1], backup_chains[-1]
			if (sig_chain.start_time == backup_chain.start_time and
				sig_chain.end_time == backup_chain.end_time):
				del sig_chains[-1]
				del backup_chains[-1]
				self.matched_chain_pair = (sig_chain, backup_chain)

		self.other_sig_chains = sig_chains
		self.other_backup_chains = backup_chains
		self.values_set = 1
		return self

	def warn(self):
		"""Log various error messages if find incomplete/orphaned files"""
		assert self.values_set
		if self.orphaned_sig_paths:
			log.Log("Warning, found the following orphaned signature files:\n"
					+ "\n".join(map(lambda x: x.name, orphaned_sig_paths)), 2)
		if self.other_sig_chains:
			if self.matched_chain_pair:
				log.Log("Warning, found unnecessary signature chain(s)", 2)
			else: log.FatalError("Found signatures but no corresponding "
								 "backup files")

		if self.incomplete_backup_sets:
			log.Log("Warning, found incomplete backup sets, probably left "
					"from aborted session", 2)
		if self.orphaned_backup_sets:
			log.Log("Warning, found the following orphaned backup files:\n"
					+ "\n".join(map(lambda x: str(x), orphaned_sets)), 2)

	def get_backup_chains(self, filename_list):
		"""Split given filename_list into chains

		Return value will be pair (list of chains, list of sets, list
		of incomplete sets), where the list of sets will comprise sets
		not fitting into any chain, and the incomplete sets are sets
		missing files.

		"""
		# First put filenames in set form
		sets = []
		def add_to_sets(filename):
			"""Try adding filename to existing sets, or make new one"""
			for set in sets:
				if set.add_filename(filename): break
			else:
				new_set = BackupSet(self.backend)
				if new_set.add_filename(filename): sets.append(new_set)
				else: log.Log("Ignoring file '%s'" % filename, 5)
		map(add_to_sets, filename_list)
		sets, incomplete_sets = self.get_sorted_sets(sets)

		chains, orphaned_sets = [], []
		def add_to_chains(set):
			"""Try adding set to existing chains, or make new one"""
			if set.type == "full":
				new_chain = BackupChain(self.backend)
				new_chain.set_full(set)
				chains.append(new_chain)
			else:
				assert set.type == "inc"
				for chain in chains:
					if chain.add_inc(set): break
				else: orphaned_sets.append(set)
		map(add_to_chains, sets)
		return (chains, orphaned_sets, incomplete_sets)

	def get_sorted_sets(self, set_list):
		"""Sort set list by end time, return (sorted list, incomplete)"""
		time_set_pairs, incomplete_sets = [], []
		for set in set_list:
			if not set.is_complete: incomplete_sets.append(set)
			elif set.type == "full": time_set_pairs.append((set.time, set))
			else: time_set_pairs.append((set.end_time, set))
		time_set_pairs.sort()
		return (map(lambda p: p[1], time_set_pairs), incomplete_sets)

	def get_signature_chains(self):
		"""Find chains present from listing self.archive_dir

		Return value is pair (list of chains, list of signature paths not
		in any chains).

		"""
		# Build initial chains from full sig filenames
		chains, new_sig_filenames = [], []
		for filename in self.archive_dir.listdir():
			pr = file_naming.parse(filename)
			if pr:
				if pr.type == "full-sig":
					new_chain = SignatureChain(self.archive_dir)
					assert new_chain.add_path(self.archive_dir
											     .append(filename), pr)
					chains.append(new_chain)
				elif pr.type == "new-sig": new_sig_filenames.append(filename)

		# Try adding new signatures to existing chains
		orphaned_paths = []
		new_sig_filenames.sort()
		for sig_filename in new_sig_filenames:
			sig_path = self.archive_dir.append(sig_filename)
			for chain in chains:
				if chain.add_path(sig_path): break
			else: orphaned_paths.append(sig_path)
		return (chains, orphaned_paths)

	def get_sorted_chains(self, chain_list):
		"""Return chains sorted by end_time"""
		pairs = map(lambda chain: (chain.end_time, chain), chain_list)
		pairs.sort()
		return map(lambda p: p[1], pairs)

	def get_backup_chain_at_time(self, time):
		"""Return backup chain covering specified time

		Tries to find the backup chain covering the given time.  If
		there is none, return the earliest chain before, and failing
		that, the earliest chain.

		"""
		if not self.all_backup_chains:
			raise CollectionsError("No backup chains found")

		covering_chains = filter(lambda c: c.start_time <= time <= c.end_time,
								 self.all_backup_chains)
		if len(covering_chains) > 1:
			raise CollectionsError("Two chains cover the given time")
		elif len(covering_chains) == 1: return covering_chains[0]

		old_chains = filter(lambda c: c.end_time < time,
							self.all_backup_chains)
		if old_chains: return old_chains[-1]
		else: return self.all_backup_chains[0] # no chains are old enough

