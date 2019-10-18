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

def try_build_dep(src):
    rc = subprocess.call(['apt-get', 'build-dep', '-y', src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc != 0:
        rc = subprocess.call(['dpkg', '--configure', '-a'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        rc = subprocess.call(['apt-get', 'build-dep', '-y', src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return rc

def build_original(src, srcpath, env):
    print("building original " + str(src))

    # Install dependencies to building the make easier
    if try_build_dep(src) != 0:
        print("\twarning: issue building dependencies for {}".format(src))
        

    # Build the package normally first to get a compile_command.json
    build_with_dpkg(srcpath, env)

    # Check for compile_command.json, and then move to tmp file so the next build doesn't
    # overwrite it 
    command_db = os.path.join(srcpath, "compile_commands.json")

    if not os.path.exists(command_db):
        print("\terror: failed to generate compile_commands.json for {}, skipping...".format(src))
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
        if warn: print("\terror: failed to build shared library for " + str(srcpath))
        return []

    built_libs = libs_3v + libs_2v
    erased_libs = [l for l in built_libs if check_elf(l)]
    if warn and len(erased_libs) == 0: print("\twarning: failed to erase libs for {}".format(srcpath)) 

    return erased_libs

def build_with_make(srcpath, env, compile_env):
    print("\ttrying to build with configure/make")
    configure_env = env.copy()
    configure_env["CFLAGS"] = "-L/usr/local/lib -llzload"
    configure_env["LDFLAGS"] = "-L/usr/local/lib -llzload"
    #rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath)
    rc = subprocess.call(['./configure'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath, env=configure_env)
    rc = subprocess.call(['make', 'clean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath, env=compile_env)
    rc = subprocess.call(['make'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=srcpath, env=compile_env)

    #rc = subprocess.call(['./configure'], cwd=srcpath, env=configure_env)
    #rc = subprocess.call(['make', 'clean'], cwd=srcpath, env=compile_env)
    #rc = subprocess.call(['make'], cwd=srcpath, env=compile_env)

def build_dummy(src, srcpath, env):
    command_db = os.path.join(srcpath, "commands.json")
                        
    print("building dummy " + str(src))

    # Start the dummy build process
    dummylib_env = env.copy()
    dummylib_env["COMPILE_COMMAND_DB"] = command_db

    build_with_dpkg(srcpath, dummylib_env)
    libs = check_erasure(srcpath, True)
    if len(libs) > 0:
        return libs

    # If we didn't find libs with __get in the ELF files, we have
    # to try ad-hoc rules
    if os.path.exists(os.path.join(srcpath, "configure")):
        build_with_make(srcpath, env, dummylib_env)
        libs = check_erasure(srcpath, True)
        if len(libs) > 0:
            return libs 
    return None 

# Anthony: Fix this
def copy_libs(libs, lib=home):
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

def build_src(src, libhome, env):
    srchome = os.path.join(working_dir,src)
    dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ]

    if len(dirs) > 1:
        print("error: multiple source directories for package: {}".format(src))
        return False
    
    srcpath = os.path.abspath(dirs[0])
    libs = gather_libs(srcpath)
    if len(check_erasure(srcpath, False)) != 0:
        print("already built " + str(src))
        return True

    rc = build_original(src, srcpath, env) 
    if not rc:
        return False

    libs = build_dummy(src, srcpath, env)
    if libs is None:
        print("\terror, could not build {} for lzload".format(src))
        return False

    copy_libs(libs, libhome)
    return True

def build_srcs(srcs, pkg_name):
    libhome = os.path.join(working_dir, "lib")
    if not os.path.exists(libhome):
        os.mkdir(libhome)

    env = os.environ.copy()

    if not env["KLLVM"]:
        print("error: Set KLLVM to point to our modified LLVM installation")
        return

    env["CC"] = os.path.join(env["KLLVM"], "build/bin/clang")
    env["CXX"] = os.path.join(env["KLLVM"], "build/bin/clang++")

    stat = open(os.path.join(working_dir, pkg_name + '.stat'), "w")
    stat.write("package name, build\n")

    for s in srcs:
        rc = build_src(s, libhome, env)
        stat.write("{},{}\n".format(s, rc))

    stat.close()
        
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

deplist = args[0]
deps=read_dependency_list(deplist)
srcs=download_src(deps)

pkgname = deplist.split('/')[-1]

build_srcs(srcs, pkgname)

