# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

# The following can be redefined to use different shell commands from
# ssh or scp or to add more arguments.  However, the replacements must
# have the same syntax.  Also these strings will be executed by the
# shell, so shouldn't have strange characters in them.

import re
import string
import time

import duplicity.backend
from duplicity import globals
from duplicity import log
from duplicity import pexpect
from duplicity.errors import *

class SSHBackend(duplicity.backend.Backend):
    """This backend copies files using scp.  List not supported"""
    def __init__(self, parsed_url):
        """scpBackend initializer"""
        duplicity.backend.Backend.__init__(self, parsed_url)

        # host string of form [user@]hostname
        if parsed_url.username:
            self.host_string = parsed_url.username + "@" + parsed_url.hostname
        else:
            self.host_string = parsed_url.hostname
        # make sure remote_dir is always valid
        if parsed_url.path:
            # remove leading '/'
            self.remote_dir = re.sub(r'^/', r'', parsed_url.path, 1)
        else:
            self.remote_dir = '.'
        self.remote_prefix = self.remote_dir + '/'
        # maybe use different ssh port
        if parsed_url.port:
            globals.ssh_options = globals.ssh_options + " -oPort=%s" % parsed_url.port
        else:
            globals.ssh_options = globals.ssh_options
        # set network timeout.  CountMax is how many retries to do, not how many tries.
        # Use CountMax=1 just in case there's a tiny network blip.
        globals.ssh_options += " -oServerAliveInterval=%i -oServerAliveCountMax=1" % ((int)(globals.timeout / 2))
        # set up password
        if globals.ssh_askpass:
            self.password = self.get_password()
        else:
            if parsed_url.password:
                self.password = parsed_url.password
                globals.ssh_askpass = True
            else:
                self.password = ''

    def run_scp_command(self, commandline):
        """ Run an scp command, responding to password prompts """
        for n in range(1, globals.num_retries+1):
            if n > 1:
                # sleep before retry
                time.sleep(30)
            log.Info("Running '%s' (attempt #%d)" % (commandline, n))
            child = pexpect.spawn(commandline, timeout = None)
            cmdloc = 0
            if globals.ssh_askpass:
                state = "authorizing"
            else:
                state = "copying"
            while 1:
                if state == "authorizing":
                    match = child.expect([pexpect.EOF,
                                          "(?i)timeout, server not responding",
                                          "(?i)pass(word|phrase .*):",
                                          "(?i)permission denied",
                                          "authenticity"])
                    log.Debug("State = %s, Before = '%s'" % (state, child.before.strip()))
                    if match == 0:
                        log.Warn("Failed to authenticate")
                        break
                    elif match == 1:
                        log.Warn("Timeout waiting to authenticate")
                        break
                    elif match == 2:
                        child.sendline(self.password)
                        state = "copying"
                    elif match == 3:
                        log.Warn("Invalid SSH password")
                        break
                    elif match == 4:
                        log.Warn("Remote host authentication failed (missing known_hosts entry?)")
                        break
                elif state == "copying":
                    match = child.expect([pexpect.EOF,
                                          "(?i)timeout, server not responding",
                                          "stalled",
                                          "authenticity",
                                          "ETA"])
                    log.Debug("State = %s, Before = '%s'" % (state, child.before.strip()))
                    if match == 0:
                        break
                    elif match == 1:
                        log.Warn("Timeout waiting for response")
                        break
                    elif match == 2:
                        state = "stalled"
                    elif match == 3:
                        log.Warn("Remote host authentication failed (missing known_hosts entry?)")
                        break
                elif state == "stalled":
                    match = child.expect([pexpect.EOF,
                                          "(?i)timeout, server not responding",
                                          "ETA"])
                    log.Debug("State = %s, Before = '%s'" % (state, child.before.strip()))
                    if match == 0:
                        break
                    elif match == 1:
                        log.Warn("Stalled for too long, aborted copy")
                        break
                    elif match == 2:
                        state = "copying"
            child.close(force = True)
            if child.exitstatus == 0:
                return
            log.Warn("Running '%s' failed (attempt #%d)" % (commandline, n))
        log.Warn("Giving up trying to execute '%s' after %d attempts" % (commandline, globals.num_retries))
        raise BackendException("Error running '%s'" % commandline)

    def run_sftp_command(self, commandline, commands):
        """ Run an sftp command, responding to password prompts, passing commands from list """
        maxread = 2000 # expect read buffer size
        responses = ["(?i)timeout, server not responding",
                     "sftp>",
                     "(?i)pass(word|phrase .*):",
                     "(?i)permission denied",
                     "authenticity",
                     "(?i)no such file or directory"]
        max_response_len = max([len(p) for p in responses])
        responses = [pexpect.EOF] + responses
        for n in range(1, globals.num_retries+1):
            if n > 1:
                # sleep before retry
                time.sleep(30)
            log.Info("Running '%s' (attempt #%d)" % (commandline, n))
            child = pexpect.spawn(commandline, timeout = None, maxread=maxread)
            cmdloc = 0
            while 1:
                match = child.expect(responses,
                                     searchwindowsize=maxread+max_response_len)
                log.Debug("State = sftp, Before = '%s'" % (child.before.strip()))
                if match == 0:
                    break
                elif match == 1:
                    log.Info("Timeout waiting for response")
                    break
                if match == 2:
                    if cmdloc < len(commands):
                        command = commands[cmdloc]
                        log.Info("sftp command: '%s'" % (command,))
                        child.sendline(command)
                        cmdloc += 1
                    else:
                        command = 'quit'
                        child.sendline(command)
                        res = child.before
                elif match == 3:
                    child.sendline(self.password)
                elif match == 4:
                    log.Warn("Invalid SSH password")
                    break
                elif match == 5:
                    log.Warn("Host key authenticity could not be verified (missing known_hosts entry?)")
                    break
                elif match == 6:
                    log.Warn("Remote file or directory does not exist in command='%s'" % (command,))
                    break
            child.close(force = True)
            if child.exitstatus == 0:
                return res
            log.Warn("Running '%s' failed (attempt #%d)" % (commandline, n))
        log.Warn("Giving up trying to execute '%s' after %d attempts" % (commandline, globals.num_retries))
        raise BackendException("Error running '%s'" % commandline)

    def put(self, source_path, remote_filename = None):
        """Use sftp to copy source_dir/filename to remote computer"""
        if not remote_filename:
            remote_filename = source_path.get_filename()
        commands = ["put %s %s%s" %
                    (source_path.name, self.remote_prefix, remote_filename)]
        commandline = ("%s %s %s" % (globals.sftp_command,
                                     globals.ssh_options,
                                     self.host_string))
        self.run_sftp_command(commandline, commands)

    def get(self, remote_filename, local_path):
        """Use sftp to get a remote file"""
        commands = ["get %s%s %s" %
                    (self.remote_prefix, remote_filename, local_path.name)]
        commandline = ("%s %s %s" % (globals.sftp_command,
                                     globals.ssh_options,
                                     self.host_string))
        self.run_sftp_command(commandline, commands)
        local_path.setdata()
        if not local_path.exists():
            raise BackendException("File %s not found locally after get "
                                   "from backend" % local_path.name)

    def list(self):
        """
        List files available for scp

        Note that this command can get confused when dealing with
        files with newlines in them, as the embedded newlines cannot
        be distinguished from the file boundaries.
        """
        commands = ["mkdir %s" % (self.remote_dir,),
                    "cd %s" % (self.remote_dir,),
                    "ls -1"]
        commandline = ("%s %s %s" % (globals.sftp_command,
                                     globals.ssh_options,
                                     self.host_string))

        l = self.run_sftp_command(commandline, commands).split('\n')[1:]

        return filter(lambda x: x, map(string.strip, l))

    def delete(self, filename_list):
        """
        Runs sftp rm to delete files.  Files must not require quoting.
        """
        commands = ["cd %s" % (self.remote_dir,)]
        for fn in filename_list:
            commands.append("rm %s" % fn)
        commandline = ("%s %s %s" % (globals.sftp_command, globals.ssh_options, self.host_string))
        self.run_sftp_command(commandline, commands)

duplicity.backend.register_backend("ssh", SSHBackend)
duplicity.backend.register_backend("scp", SSHBackend)
