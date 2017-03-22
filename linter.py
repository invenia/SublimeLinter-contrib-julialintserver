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
import sublime

from time import sleep
from SublimeLinter.lint import Linter, util, persist

PKG_DIR = os.path.dirname(os.path.realpath(__file__))


class JuliaLintServerDaemon(object):
    """Singleton class that handles communication with the actual lint server."""

    __instance = None

    def __new__(cls, address, port, auto_start=True, timeout=60,
                python3="python3", julia="julia"):
        """Constructor."""
        if JuliaLintServerDaemon.__instance is None:
            JuliaLintServerDaemon.__instance = object.__new__(cls)
            JuliaLintServerDaemon.__instance.proc = None

        JuliaLintServerDaemon.__instance.address = address
        JuliaLintServerDaemon.__instance.port = port
        JuliaLintServerDaemon.__instance.auto_start = auto_start
        JuliaLintServerDaemon.__instance.timeout = timeout
        JuliaLintServerDaemon.__instance.python3 = python3
        JuliaLintServerDaemon.__instance.julia = julia

        return JuliaLintServerDaemon.__instance

    def _lint(self, path, content, file_messages_only=True):
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

        # Only return the warnings in the linted file
        if(file_messages_only):
            # persist.debug("All messages for {}:\n{}".format(path, response.strip()))
            file_messages = ""
            for line in response.splitlines():
                if re.match(r'^{}.*$'.format(re.escape(path)), line):
                    file_messages += line + '\n'
            response = file_messages

        return response

    def start(self):
        """Start a Julia Lint server on the localhost."""
        if self.proc is not None:
            return

        server_script = os.path.join(
            sublime.packages_path(), "SublimeLinter-contrib-julialintserver",
            "bin", "julia-lint-server"
        )

        cmd = [
            self.python3,
            server_script,
            "--port",
            str(self.port),
            "--julia",
            self.julia
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


class JuliaLintServer(Linter):
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
        "path_to_python3": "python3",
        "path_to_julia": "julia"
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
        cls.server = JuliaLintServerDaemon(
            settings['server_address'],
            settings['server_port'],
            settings['automatically_start_server'],
            settings['timeout'],
            settings['path_to_python3'],
            settings['path_to_julia']
        )

        warn_levels = ['W\d\d\d']
        if settings['show_info_warnings']:
            warn_levels.append('I\d\d\d')

        # Set the regex based upon whether or not show_info_warnings is set
        cls.regex = re.compile(
            r"""
            ^(?P<filename>.+?\.jl):(?P<line>\d+)
            \s+
            (?P<message>
                (?:
                    (?P<error>E\d\d\d)
                    |
                    (?P<warning>{})
                )
                \s+
                (?:
                    (?P<near>.*?):\s
                )
                \s*
                .*?
            )
            \s*$
            """.format("|".join(warn_levels)),
            re.VERBOSE,
        )

    def run(self, cmd, code):
        """Override the run function. Returns a string containing the output."""
        return self.server.lint(self.filename, code)
