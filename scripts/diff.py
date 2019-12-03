#!/usr/bin/env python3

import os.path
import sys

f1 = set()
with open(sys.argv[1]) as f:
    for l in f.readlines():
        f1.add(l.strip())

f2 = set()
with open(sys.argv[2]) as f:
    for l in f.readlines():
        f2.add(l.strip())

f3 = f2 - f1
with open("diff.txt", "w") as f:
    for i in f3:
        f.write(i + "\n")

f3 = f2 & f1
with open("union.txt", "w") as f:
    for i in f3:
        f.write(i + "\n")
