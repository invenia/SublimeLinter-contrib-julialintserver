#
# linter.py
# Linter for SublimeLinter3, a code checking framework for Sublime Text 3
#
# Written by Michael Klassen
# Copyright (c) 2015 Invenia Technical Computing Corporation
#
# License: MIT
#

"""This module exports the Julialintserver plugin class."""

import subprocess
import os
import re
import time
import socket

from SublimeLinter.lint import Linter, util, persist


def call_server(path, code, address, port, timeout=60):
    """Pass message to a juliaLint server at given address and port and return the response."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((address, port))
    s.sendall(bytes("".join([
        path,  # Send path so server can check for dependencies
        "\n",
        str(len(bytes(code, 'UTF-8'))),  # Send number of bytes in code so server knows how much to receive
        "\n",
        code,  # Send the actual code
    ]), "UTF-8"))

    # Receive messages. Lint Server sends a empty newline when there are no more messages
    response = s.recv(4096).decode("utf-8")
    # Look at the last 2 chars; 2 newlines is an empty line or if only a single char was receive and is a newline
    while response[-2:] not in ('\n\n', '\n'):
        response += s.recv(4096).decode("utf-8")
    s.close()
    return response


def launch_julialintserver(port):
    """Run the julia lintserver script."""
    serverscript = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lint/runjulialintserver.py')
    cmd = ['python3', serverscript, str(port)]
    proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, env=util.create_environment())
    return proc


class Julialintserver(Linter):
    """Provides an interface to julia lintserver."""

    syntax = 'julia'
    cmd = None
    executable = None
    version_args = None
    version_re = None
    version_requirement = None
    regex = r''

    def set_regex(self):
        """Set the regex variable. We want a different regex depending on wether or not show_info_warnings is set."""
        settings = self.get_merged_settings()
        warn_levels = ['WARN']
        if settings['show_info_warnings']:
            warn_levels.append('INFO')

        regex = re.compile(
            r"""
            ^(?P<filename>.+?\.jl):(?P<line>\d+)
            \s+
            \[(?P<near>.*?)\s*\]
            \s+
            (?P<message>
                (?:
                    (?P<error>ERROR|FATAL)
                    |
                    (?P<warning>{})
                )
                \s+
                .*?
            )
            \s*$
            """.format("|".join(warn_levels)),
            re.VERBOSE,
        )
        self.regex = regex

    multiline = False
    line_col_base = (1, 1)
    tempfile_suffix = 'jl'
    error_stream = util.STREAM_BOTH
    selectors = {}
    word_re = None
    defaults = {
        'show_info_warnings': False,
        'server_address': 'localhost',
        'server_port': 2222,
        'automatically_start_server': True,
        'timeout': 30,
    }
    inline_settings = None
    inline_overrides = None
    comment_re = None

    Julialintserver_proc = None

    def run(self, cmd, code):
        """Override the run function. Returns a string containing the julia lintserver's output."""
        self.set_regex()
        # Get user settings
        settings = self.get_merged_settings()
        address = settings['server_address']
        port = settings['server_port']
        autostart = settings['automatically_start_server']
        timeout = settings['timeout']

        output = ""
        try:
            persist.debug("Connecting to julia lintsever({}, {})".format(address, port))
            output = call_server(self.filename, code, address, port, timeout=timeout)
        except Exception as e:
            persist.debug("Sever connection unsuccessful: {}".format(e))
            if self.Julialintserver_proc is not None:
                if self.Julialintserver_proc.poll() is not None:
                    raise subprocess.SubprocessError(self.Julialintserver_proc.returncode)
                else:
                    persist.debug("Local Julia lintserver was started.")
            elif autostart:
                persist.printf("Launching julia lintserver on localhost port {}".format(port))

                self.Julialintserver_proc = launch_julialintserver(port)
                # Set address to localhost for new julia lintserver
                address = 'localhost'

                persist.printf("julia lintserver starting up, server will be operational in approximately 30 seconds")
                try:
                    # Let julia launch
                    time.sleep(5)
                    # Run once with high timeout to let julia compile all appropriate functions
                    output = call_server(self.filename, code, address, port, timeout=timeout+60)
                    persist.printf("julia lintserver now operational")
                except Exception as e:
                    persist.printf("julia lintserver failed to start properly.")
            else:
                persist.debug("Automatically_start_server is currently false.")

        return output
