#!/usr/bin/env python3.6

import subprocess
import os.path
import sys
import glob
import shutil

from optparse import OptionParser 

import json
import re

ARCH='x86_64-linux-gnu'
working_dir = ""

EXCLUDES=["libc6", "libgcc1", "gcc-8-base", "<debconf-2.0>", "debconf"]
KLLVM = "/home/acanino/llvm/build/bin"

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

    compile_db_env = os.environ.copy()
    compile_db_env["CC"] = os.path.join(KLLVM, "clang")
    compile_db_env["CXX"] = os.path.join(KLLVM, "clang++")

    for s in srcs:
        srchome = os.path.join(working_dir,s)
        dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ]

        if len(dirs) > 1:
            print("Error: multiple source directories for package: {}".format(s))
            continue
        
        srcpath = os.path.abspath(dirs[0])

        print("building original " + str(s))

        # Install dependencies to building the make easier
        rc = subprocess.call(['apt-get', 'build-dep', '-y', s], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Build the package normally first to get a compile_command.json
        rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath)
        rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath, env=compile_db_env)

        # Check for compile_command.json, and then move to tmp file so the next build doesn't
        # overwrite it 
        command_db = os.path.join(srcpath, "compile_commands.json")

        if not os.path.exists(command_db):
            print("Error: failed to generate compile_commands.json for {}, skipping...".format(s))
            continue
        # Tmp

        shutil.copy(command_db, os.path.join(srcpath, "commands.json"))
        command_db = os.path.join(srcpath, "commands.json")
        
        print("building dummy " + str(s))

        # Start the dummy build process
        dummylib_env = compile_db_env.copy()
        dummylib_env["COMPILE_COMMAND_DB"] = command_db

        rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath)
        rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath, env=dummylib_env)
        #rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stderr=subprocess.STDOUT, cwd=srcpath)
        #rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], stderr=subprocess.STDOUT, cwd=srcpath, env=dummylib_env)

        # Anthony : Hacking, will come back to systematically find the right libs
        hiddenlibs = glob.glob(os.path.join(srcpath, "**/.libs/**.so*"), recursive=True) 
        normallibs = glob.glob(os.path.join(srcpath, "**/**.so*"), recursive=True) 
        libs = hiddenlibs + normallibs

        libs_3v = [l for l in libs if re.match(".*\.so\.\d+\.\d+\.\d+$", l)]

        libs_2v = [l for l in libs if re.match(".*\.so\.\d+\.\d+$", l)]

        if len(libs_3v) == 0 and len(libs_2v) == 0:
            print("Error: failed to build shared library for " + str(s))
            continue
    
        for l in libs_3v:
            libname = l.split("/")[-1]
            print("\tbuilt {}".format(libname))
            # Copy raw
            shutil.copy(l, libhome)
            # Create "version"
            toks = libname.split(".")
            version = ".".join(toks[0:-2])
            path = os.path.join(libhome,version)
            shutil.copy(l, os.path.join(libhome, version))

        for l in libs_2v:
            libname = l.split("/")[-1]
            print("\tbuilt {}".format(libname))
            shutil.copy(l, libhome)

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

