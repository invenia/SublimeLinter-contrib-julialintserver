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

from SublimeLinter.lint import Linter, util


def create_tmpfile(filename, suffix, code):
    """Create a temp file and return the path to it. Call remove_tmpfile(path) to remove."""
    if not filename:
        filename = util.UNSAVED_FILENAME
    else:
        filename = os.path.basename(filename)

    if suffix:
        filename = os.path.splitext(filename)[0] + suffix

    path = os.path.join(util.tempdir, filename)
    with open(path, mode='wb') as f:
            if isinstance(code, str):
                code = code.encode('utf-8')

                f.write(code)
                f.flush()

    return os.path.abspath(path)


def remove_tmpfile(path):
    """Remove the temp file created by create_tmpfile."""
    os.remove(path)


def call_server(message, address, port):
    """Pass message to a juliaLint server at given address and port and return the response."""
    command = "(echo " + str(message) + "; sleep 2 ) | nc -w 2 " + str(address) + " " + str(port)
    return subprocess.check_output(command, shell=True).decode("utf-8")


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
        'server_port': 2222
    }
    inline_settings = None
    inline_overrides = None
    comment_re = None

    def run(self, cmd, code):
        """Override the run function. Returns a string containing the julia lint server's output."""
        self.set_regex()
        settings = self.get_merged_settings()
        path = create_tmpfile(self.filename, self.get_tempfile_suffix(), code)
        output = "Error"
        try:
            output = call_server(path, settings['server_address'], settings['server_port'])
        finally:
            remove_tmpfile(path)

        return output
