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
import socket

from time import sleep
from SublimeLinter.lint import Linter, util, persist

PKG_DIR = os.path.dirname(os.path.realpath(__file__))


class JuliaLintServer(object):
    """Singleton class that handles communication with the actual lint server."""

    __instance = None

    def __new__(cls, address, port, auto_start=True, timeout=60):
        """Constructor."""
        if JuliaLintServer.__instance is None:
            JuliaLintServer.__instance = object.__new__(cls)
            JuliaLintServer.__instance.proc = None

        JuliaLintServer.__instance.address = address
        JuliaLintServer.__instance.port = port
        JuliaLintServer.__instance.auto_start = auto_start
        JuliaLintServer.__instance.timeout = timeout

        return JuliaLintServer.__instance

    def _lint(self, path, content):
        """Send lint request to server."""
        # First convert the content into bytes so we can get an accurate count
        content = bytes(content, "UTF-8")

        # Format the message to send to the server. Including the length
        # of the content so the server knows where the content ends.
        # Note: Path is included so server can check for dependencies
        message = b"\n".join([
            bytes(path, "UTF-8"),
            bytes(str(len(content)), "UTF-8"),
            content,
        ])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect((self.address, self.port))
        s.sendall(message)

        # TODO: Probably would be best to return a stream
        response = s.recv(4096).decode("UTF-8")
        while response[-2:] not in ('\n\n', '\n'):
            response += s.recv(4096).decode("UTF-8")
        s.close()

        return response

    def start(self):
        """Start a Julia Lint server on the localhost."""
        if self.proc is not None:
            return

        cmd = [
            os.path.join(PKG_DIR, 'bin', 'julia-lint-server'),
            str(self.port),
        ]

        # Note: We'll spawn a intermediate subprocess which will
        # automatically shutdown the server. This extra process is only
        # necessary since there appears to be no way to handle a sublime
        # exit event (neither signals, atexit, or sublime provide a way
        # to do this)
        # https://github.com/SublimeTextIssues/Core/issues/10
        self.proc = subprocess.Popen(
            cmd,
            stderr=subprocess.STDOUT,
            env=util.create_environment(),
        )

    def lint(self, path, content):
        """Lint the content of a file."""
        output = ""
        try:
            persist.debug("Connecting to Julia lint server ({}, {})".format(self.address, self.port))  # noqa
            output = self._lint(path, content)
        except Exception as e:
            persist.debug(e)

            if not self.auto_start:
                persist.printf("Julia lint server is not running")
            else:
                # if self.proc is not None:
                #     if self.proc.poll() is None:
                #         persist.debug("Local Julia lint server was started")
                #         return
                #     else:
                #        raise subprocess.SubprocessError(self.proc.returncode)

                persist.printf("Launching Julia lint server on localhost port {}".format(self.port))  # noqa
                self.start()

                persist.printf("Julia lint server starting up, server will be operational shortly")  # noqa
                try:
                    # Wait to give Julia time to start
                    sleep(5)

                    output = self._lint(path, content)
                except Exception as e:
                    persist.debug(e)
                    persist.printf("Julia lint server failed to start")
                else:
                    persist.printf("Julia lint server now operational")

        return output


class Julia(Linter):
    """Provides an interface to Julia lintserver."""

    syntax = 'julia'
    cmd = None
    executable = None
    version_args = None
    version_re = None
    version_requirement = None
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

    regex = r''
    server = None

    @classmethod
    def initialize(cls):
        """Initialize."""
        persist.printf(cls)
        super().initialize()
        settings = cls.settings()

        # Server will a
        cls.server = JuliaLintServer(
            settings['server_address'],
            settings['server_port'],
            settings['automatically_start_server'],
            settings['timeout'],
        )

        warn_levels = ['WARN']
        if settings['show_info_warnings']:
            warn_levels.append('INFO')

        # Set the regex based upon whether or not show_info_warnings is set
        cls.regex = re.compile(
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

    def run(self, cmd, code):
        """Override the run function. Returns a string containing the output."""
        return self.server.lint(self.filename, code)
