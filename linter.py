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
import tempfile
import time

from SublimeLinter.lint import Linter, util, persist


def open_tmpfile(filename, suffix, code):
    """Open and return a tempfile with the code in it. Remember to close this file."""
    if not filename:
        basename = util.UNSAVED_FILENAME
        dirname = util.tempdir
    else:
        dirname, basename = os.path.split(filename)

    if suffix:
        basename = os.path.splitext(basename)[0] + suffix

    f = tempfile.NamedTemporaryFile(dir=dirname, suffix=basename)
    try:
        if isinstance(code, str):
            code = code.encode('utf-8')

            f.write(code)
            f.flush()
    except:
        f.close()

    return f


def call_server(message, address, port, timeout=2, sleep=2):
    """Pass message to a juliaLint server at given address and port and return the response."""
    command = ('(echo {}; sleep {}) | nc -w {} {} {}'.format(message, sleep, timeout, address, port))
    return subprocess.check_output(command, shell=True).decode("utf-8")


def launch_local_server(port):
    """launch a julia lintserver."""
    serverscript = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lint/runjuliaserver.py')
    cmd = ['python3', serverscript, str(port)]
    proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, env=util.create_environment())
    return proc


class Julialintserver(Linter):
    """Provides an interface to julialintserver."""

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
        'automatically_start_server': True
    }
    inline_settings = None
    inline_overrides = None
    comment_re = None

    proc = None

    def run(self, cmd, code):
        """Override the run function. Returns a string containing the julia lintserver's output."""
        self.set_regex()

        settings = self.get_merged_settings()
        address = settings['server_address']
        port = settings['server_port']
        autostart = settings['automatically_start_server']

        output = "An unknown error has occured when trying to connect to server."

        f = open_tmpfile(self.filename, self.get_tempfile_suffix(), code)
        try:
            persist.debug("Calling sever({}, {}) with file".format(address, port))
            output = call_server(f.name, address, port)
        except Exception as e:
            persist.debug("Calling sever failed: {}".format(e))
            if self.proc is not None:
                if self.proc.poll() is not None:
                    raise subprocess.SubprocessError(self.proc.returncode())
                else:
                    output = "Local Julia lintserver was started."
            elif autostart:
                persist.printf("Launching julia lintserver on localhost port {}".format(port))

                self.proc = launch_local_server(port)
                address = 'localhost'

                persist.printf(
                    "julia lintserver starting up, server will be operational in about 30 seconds".format(self.proc.pid)
                )
                try:
                    # Let julia launch
                    time.sleep(5)
                    # Run once with high timeout to make julia compile all appropriate function
                    call_server(f.name, address, port, timeout=60)
                    time.sleep(5)
                    # Lint file
                    output = call_server(f.name, address, port)
                except:
                    persist.debug("Local Julia lintserver failed to start properly.")
                    output = "Local Julia lintserver failed to start properly."
            else:
                persist.debug("Failed to connect to julia lintserver. automatically_start_server is currently false.")
                output = "Failed to connect to julia lintserver. automatically_start_server is currently false."
        finally:
            f.close()

        return output
