#!/usr/bin/env python3

import os.path
from optparse import OptionParser 
import re
    
usage = "usage: %prog [options] dependency-list"
parser = OptionParser(usage=usage)
parser.add_option('-d', '--dir', dest='working_dir', default='symbol-out', help='use DIR as working output directory', metavar='DIR')

(options, args) = parser.parse_args()

working_dir = options.working_dir

libs = []
for l in os.listdir(os.path.join(working_dir, "lib")):
    if re.match(".*\.so\d+$", l) or re.match(".*\.so\.\d+$", l) or re.match(".*\.so\.\d+\.\d+$", l):
        libs.append(l)

print("export LZLOAD_LIB=\"", end="")

for l in libs:
    print(l + ":", end="")
print("\"")
