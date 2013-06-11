"""Store global configuration information"""

# The current version of duplicity
version = "0.0.2"

# If true, filelists and directory statistics will be split on
# nulls instead of newlines.
null_separator = None

# Path of duplicity directory (usually $HOME/.duplicity)
dupdir = None

# Character used like the ":" in time strings like
# 2002-08-06T04:22:00-07:00.  The colon isn't good for filenames on
# windows machines.
time_separator = ":"
