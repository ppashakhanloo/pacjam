#!/usr/bin/env python3

import os.path
import shutil
import sys

srcs = sys.argv[1]
dest = sys.argv[2]
deps = sys.argv[3]

with open(deps, "r") as d:
    for i in d.readlines():
        for pat in ["", ".original", ".dpkg", ".make", ".vararg"]:
            sp = os.path.join(srcs, i.strip() + pat)
            if os.path.exists(sp):
                print("Copying " + sp)
                shutil.copytree(sp, os.path.join(dest, i.strip() + pat), symlinks=True)
