"""Store global configuration information"""

# The current version of duplicity
version = "0.1.1"

# If true, filelists and directory statistics will be split on
# nulls instead of newlines.
null_separator = None

# Path of duplicity directory (usually $HOME/.duplicity)
dupdir = None

# Character used like the ":" in time strings like
# 2002-08-06T04:22:00-07:00.  The colon isn't good for filenames on
# windows machines.
time_separator = ":"

# Set to the Path of the archive directory (the directory which
# contains the signatures and manifests of the relevent backup
# collection.
archive_dir = None

# If set, use this value as the current time in seconds instead of
# reading from the clock.
current_time = None

# Restores will try to bring back the state as of the following time.
# If it is None, default to current time.
restore_time = None

# If set, use public key encryption to listed keys when backing up,
# otherwise use symmetric encryption.
encryption_keys = []

# If set, when encrypting sign with this key, and when decrypting
# require that the file be signed with this key.
sign_key = None

