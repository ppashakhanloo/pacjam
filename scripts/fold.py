#!/usr/bin/env python3

import os.path
import glob
from optparse import OptionParser 

usage = "usage: %prog [options]" 
parser = OptionParser(usage=usage)
parser.add_option('-d', '--dir', dest='working_dir', default='.', help='use DIR as working output directory', metavar='DIR') 
parser.add_option('-p', '--preserve', dest='preserve', action='store_true', help='preserve process trace files (do not delete)')

(options, args) = parser.parse_args()

tracename = "lzload.trace"
if "LZLOAD_TRACE" in os.environ:
    tracename = os.environ["LZLOAD_TRACE"]

files = glob.glob("{}/{}.*".format(options.working_dir, tracename))
used = set()
for fn in files:
    print("merging {}".format(fn))
    with open(fn, "r") as f:
        iused = set(f.readlines()[0].split())
        if "nodep" not in iused:
            used.update(iused)
    if not options.preserve:
        os.remove(fn)

with open("{}/{}".format(options.working_dir, tracename), "a") as f:
    if len(used) > 0:
        for d in used:
            f.write(d + " ")
        f.write("\n")
    else:
        f.write("nodep\n")
