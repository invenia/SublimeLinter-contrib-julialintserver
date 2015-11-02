"""Launch a Julia lintserver and when this process becomes an orphan it will suicide and kill the server."""

import sys
import time
import subprocess
import os
import signal


def sigterm_handler(_signo, _stack_frame):
    """Kill proc the sys.exit."""
    if proc:
        proc.kill()
    # Raises SystemExit(0):
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

args = sys.argv
if len(args) != 2:
    print("runjuliaserver.py <port>")
    sys.exit(2)

port = args[1]

parent = os.getppid()

cmd = 'julia -e "using Lint; lintserver({})"'.format(port)

proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, env=os.environ)
while os.getppid() == parent and proc.poll() is None:
        time.sleep(0.1)
proc.kill()
