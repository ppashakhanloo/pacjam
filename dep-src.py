#!/usr/bin/env python3.6

import subprocess
import os.path
import sys
import glob
import shutil

from optparse import OptionParser 

import json

ARCH='x86_64-linux-gnu'
working_dir = ""

EXCLUDES=["libc6", "libgcc1", "gcc-8-base", "<debconf-2.0>", "debconf"]
KLLVM = "/home/acanino/local-llvm/llvm/build/bin"

def read_dependency_list(name):
    deps = {}
    with open(name, 'r') as f:
        for d in f.read().splitlines():
            deps[d] = True
    return deps

def download_src(deps):
    srcs = []

    for d in deps:
        if exclude_src(d, EXCLUDES):
            continue

        print('fetching ' + d)
        try:
            srchome = os.path.join(working_dir,d)
            if not os.path.exists(srchome):
                os.mkdir(srchome)
                out = subprocess.check_output(['apt-get', 'source', d], stderr=subprocess.STDOUT, cwd=srchome)
            srcs.append(d)
        except IOError as e:
            print(e)
        except subprocess.CalledProcessError as e:
            print(e)

    return srcs

def build_srcs(srcs):
    libhome = os.path.join(working_dir, "lib")
    if not os.path.exists(libhome):
        os.mkdir(libhome)

    compiledb_env = os.environ.copy()
    compiledb_env["CC"] = os.path.join(KLLVM, "clang")
    compiledb_env["CXX"] = os.path.join(KLLVM, "clang++")
    compiledb_env["DUMMY_LIB_GEN"] = "OFF"

    for s in srcs:
        srchome = os.path.join(working_dir,s)
        dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ]

        if len(dirs) > 1:
            print("Error: multiple source directories for package: {}".format(s))
            continue

        #libs = glob.glob(os.path.join(dirs[0], "**/*.so"), recursive=True) 
        # Already built
        #if len(libs) > 0:
        #    print("already built " + str(s))
        #    continue

        print("building original " + str(s))

        # Install dependencies to building the make easier
        rc = subprocess.call(['apt-get', 'build-dep', '-y', s], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Build the package normally first to get a compile_command.json
        rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=dirs[0])
        rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=dirs[0], env=compiledb_env)

        print("Working in dir {} looking for {}".format(dirs[0], command_db))


        # Check for compile_command.json, and then move to tmp file so the next build doesn't
        # overwrite it 
        command_db = os.path.join(dirs[0], "compile_command.json")
        if not os.path.exists(command_db):
            print("Error: failed to generate compile_command.json for {}, skipping...".format(s))
            continue
        # Tmp
        continue

        shutil.copy(command_db, os.path.join(dirs[0], "command.json"))
        command_db = os.path.join(dirs[0], "command.json")
        
        print("building dummy " + str(s))

        # Start the dummy build process
        dummylib_env = compiledb_env.copy()
        dummylib_env["DUMMY_LIB_GEN"] = "ON"
        dummylib_env["COMPILE_COMMAND_PATH"] = command_db

        rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=dirs[0])
        rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=dirs[0], env=dummylib_env)

        # Anthony : Hacking, will come back to systematically find the right libs
        libs = glob.glob(os.path.join(dirs[0], "**/.libs/*.so.*"), recursive=True) 
        if len(libs) == 0:
            libs = glob.glob(os.path.join(dirs[0], "**/*.so.*"), recursive=True) 

        if len(libs) == 0:
            print("Error: failed to build shared library for " + str(s))
            continue
    
        #for l in libs:
        #    if os.path.islink(l): 
        #        continue
        #    shutil.copy(l, libhome)

#STDOUT From Anthony, this is very hacky and ugly, but for now while we are designing the
# system, I'll just keep it as is.
def exclude_src(dep, excludes):
    for e in excludes:
        if dep in e:
            return True
    return False

usage = "usage: %prog [options] dependency-list"
parser = OptionParser(usage=usage)
parser.add_option('-d', '--dir', dest='working_dir', default='symbol-out', help='use DIR as working output directory', metavar='DIR')

(options, args) = parser.parse_args()

working_dir = options.working_dir

if len(args) < 1:
    print("error: must supply dependency-list")
    parser.print_usage()
    sys.exit(1)

deps=read_dependency_list(args[0])
srcs=download_src(deps)
build_srcs(srcs)

