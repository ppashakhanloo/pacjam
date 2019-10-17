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

def gather_libs(path):
    out = subprocess.run(['find',path, '-name', 'lib*.so*'], stdout=subprocess.PIPE)
    libs = []
    for l in out.stdout.splitlines():
        libs.append(l.decode('utf-8'))
    return libs

def check_elf(path):
    readelf = subprocess.Popen(['readelf', '-Ws', path], stdout=subprocess.PIPE)
    out = subprocess.run(['grep','__get'], stdout=subprocess.PIPE, stdin=readelf.stdout)
    return len(out.stdout) > 0

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

def build_with_dpkg(path, env):
    rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path, env=env)

def build_original(src, srcpath, env):
    print("building original " + str(src))

    # Install dependencies to building the make easier
    rc = subprocess.call(['apt-get', 'build-dep', '-y', src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Build the package normally first to get a compile_command.json
    build_with_dpkg(srcpath, env)

    # Check for compile_command.json, and then move to tmp file so the next build doesn't
    # overwrite it 
    command_db = os.path.join(srcpath, "compile_commands.json")

    if not os.path.exists(command_db):
        print("Error: failed to generate compile_commands.json for {}, skipping...".format(src))
        return False
    # Tmp

    shutil.copy(command_db, os.path.join(srcpath, "commands.json"))
    return True

def check_erasure(srcpath, warn):
    # Anthony : Hacking, will come back to systematically find the right libs
    libs = gather_libs(srcpath)
    libs_3v = [l for l in libs if re.match(".*\.so\.\d+\.\d+\.\d+$", l)]
    libs_2v = [l for l in libs if re.match(".*\.so\.\d+\.\d+$", l)]

    if len(libs_3v) == 0 and len(libs_2v) == 0:
        if warn:
            print("Error: failed to build shared library for " + str(srcpath))
        return None

    built_libs = libs_3v + libs_2v
    for l in built_libs:
        if not check_elf(l): 
            if warn:
                print("\twarning: {} was not erased".format(l))
            return None

    return libs

def build_with_make(srcpath, env, compile_env):
    print("\ttrying to build with configure/make")
    configure_env = env.copy()
    configure_env["CFLAGS"] = "-L/usr/local/lib -llzload"
    configure_env["LDFLAGS"] = "-L/usr/local/lib -llzload"
    rc = subprocess.call(['./configure'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath, env=configure_env)
    rc = subprocess.call(['make'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath, env=compile_env)

def build_dummy(src, srcpath, env):
    command_db = os.path.join(srcpath, "commands.json")
                        
    print("building dummy " + str(src))

    # Start the dummy build process
    dummylib_env = env.copy()
    dummylib_env["COMPILE_COMMAND_DB"] = command_db

    build_with_dpkg(srcpath, dummylib_env)
    libs = check_erasure(srcpath, True)
    if libs is not None:
        return libs

    # If we didn't find libs with __get in the ELF files, we have
    # to try ad-hoc rules
    if os.path.exists(os.path.join(srcpath, "configure")):
        build_with_make(srcpath, env, dummylib_env)
        libs = check_erasure(srcpath, True)
        if libs is not None:
            return libs

    return None


# Anthony: Fix this
def copy_libs(libs, libhome):
    copied = {}
    for l in libs:
        libname = l.split("/")[-1]
        toks = libname.split(".")

        if len(toks) == 2 or toks[0] in copied:
            continue

        print("\tbuilt {}".format(".".join(toks)))

        if len(toks) == 5:
            shutil.copy(l, libhome)
            # Create "version"
            toks = libname.split(".")
            version = ".".join(toks[0:-2])
            path = os.path.join(libhome,version)
            shutil.copy(l, path)
        else:
            shutil.copy(l, libhome)
        
        copied[toks[0]] = True



    #for l in libs_3v:
    #    libname = l.split("/")[-1]
    #    print("\tbuilt {}".format(libname))
    #    # Copy raw
    #    shutil.copy(l, libhome)
    #    # Create "version"
    #    toks = libname.split(".")
    #    version = ".".join(toks[0:-2])
    #    path = os.path.join(libhome,version)
    #    shutil.copy(l, path)
    #    
    #for l in libs_2v:
    #    libname = l.split("/")[-1]
    #    print("\tbuilt {}".format(libname))
    #    shutil.copy(l, libhome)
    #    if not check_elf(os.path.join(libhome,l)):
    #        print("\twarning: {} was not erased".format(libname))

def build_srcs(srcs):
    libhome = os.path.join(working_dir, "lib")
    if not os.path.exists(libhome):
        os.mkdir(libhome)

    env = os.environ.copy()

    if not env["KLLVM"]:
        print("Error: Set KLLVM to point to our modified LLVM installation")
        return

    env["CC"] = os.path.join(env["KLLVM"], "build/bin/clang")
    env["CXX"] = os.path.join(env["KLLVM"], "build/bin/clang++")

    for s in srcs:
        srchome = os.path.join(working_dir,s)
        dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ]

        if len(dirs) > 1:
            print("Error: multiple source directories for package: {}".format(s))
            continue
        
        srcpath = os.path.abspath(dirs[0])
        libs = gather_libs(srcpath)
        if not check_erasure(srcpath, False):
            rc = build_original(s, srcpath, env) 
            if not rc: continue

            libs = build_dummy(s, srcpath, env)
            if libs is None:
                print("\tesrror, could not build {} for lzload".format(s))
                continue

            copy_libs(libs, libhome)
        else:
            print("already built " + str(s))

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

