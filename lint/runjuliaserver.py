"""Launch a Julia lintserver then poll ppid. When this process becomes an orphan it will suicide and kill the server."""

import sys
import time
import subprocess
import os


args = sys.argv
if len(args) != 2:
    print("runjuliaserver.py <port>")
    sys.exit(2)

port = args[1]

parent = os.getppid()

cmd = 'julia -e "using Lint; lintserver({})"'.format(port)

with subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, env=os.environ) as proc:
    while True:
        if os.getppid() == parent:
            time.sleep(0.1)
        else:
            proc.kill()
            sys.exit()
