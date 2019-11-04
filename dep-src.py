#!/usr/bin/env python3

import subprocess
import os.path
import sys
import glob
import shutil

from optparse import OptionParser 

import json
import re

REPO_HOME = os.path.dirname(os.path.realpath(__file__))
COMPILATION_DB_DIR_PATH = os.path.join(REPO_HOME, "compilation_db")

ARCH='x86_64-linux-gnu'
working_dir = ""

EXCLUDES=["libc6", "libgcc1", "gcc-8-base", "<debconf-2.0>", "debconf", "libselinux1", "libzstd1", "libstdc++6", "dpkg", "tar", "perl-base", "install-info"]

CONFIG_OPTS={ "libtinfo6": ["--with-shared", "--with-termlib"], "libncurses6": ["--with-shared"], "libncursesw6": ["--with-shared"],
              "libopus0": ["--disable-maintainer-mode"], "libprotobuf-lite17": ["--disable-maintainer-mode", "--disable-dependency-tracking"] }

MAKE_ONLY=["libbluray2", "libprotobuf-lite17"]

ORIGINAL=".original"
DPKG=".dpkg"
MAKE=".make"

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
            if d.startswith('#'):
                continue
            deps[d] = True
    return deps

def download_src(dep):
    try:
        srchome = os.path.join(working_dir,dep)
        if not os.path.exists(srchome):
            os.mkdir(srchome)
            out = subprocess.check_output(['apt-get', 'source', dep], stderr=subprocess.STDOUT, cwd=srchome)
        return True
    except IOError as e:
        print(e)
        return False
    except subprocess.CalledProcessError as e:
        print(e) 
        return False 

def download_srcs(deps):
    srcs = []

    for d in deps:
        if exclude_src(d, EXCLUDES):
            continue

        print('fetching ' + d)
        if download_src(d):
            srcs.append(d)

    return srcs

def build_with_dpkg(path, env, parallel=False):
    rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], stdout=log, stderr=subprocess.STDOUT, cwd=path)
    if parallel:
        rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b', '-j32'], stdout=log, stderr=subprocess.STDOUT, cwd=path, env=env)
    else:
        rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], stdout=log, stderr=subprocess.STDOUT, cwd=path, env=env)
    #rc = subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-Tclean'], cwd=path)
    #rc = subprocess.call(['dpkg-buildpackage', '-us', '-uc', '-d', '-b'], cwd=path, env=env)

def try_build_dep(src):
    rc = subprocess.call(['apt-get', 'build-dep', '-y', src], stdout=log, stderr=subprocess.STDOUT)
    if rc != 0:
        rc = subprocess.call(['dpkg', '--configure', '-a'], stdout=log, stderr=subprocess.STDOUT)
        rc = subprocess.call(['apt-get', 'build-dep', '-y', src], stdout=log, stderr=subprocess.STDOUT)
    return rc

def build_original(src, env):
    print("building original " + str(src))

    srchome = copy_src(os.path.join(working_dir, src), ORIGINAL)

    dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ]

    if len(dirs) > 1:
        print("error: multiple source directories for package: {}".format(src))
        return None, None
    if len(dirs) == 0:
        print("error: no source directories for package: {}".format(src))
        return None, None

    srcpath = dirs[0]

    # Install dependencies to building the make easier
    if try_build_dep(src) != 0:
        print("\twarning: issue building dependencies for {}".format(src)) 

    saved_command_db = os.path.join(*[COMPILATION_DB_DIR_PATH, src, "compile_commands.json"])
    if os.path.exists(saved_command_db):
        print("\twarning: reuse saved compilation db")
    else:
        # Build the package normally first to get a compile_command.json
        build_with_dpkg(srcpath, env)

        # Check for compile_command.json, and then move to tmp file so the next build doesn't
        # overwrite it 
        command_db = os.path.join(srcpath, "compile_commands.json")

        if not os.path.exists(command_db):
            print("\terror: failed to generate compile_commands.json for {}, skipping...".format(src))
            return None, None

        os.makedirs(os.path.dirname(saved_command_db), exist_ok=True)
        shutil.copy(command_db, saved_command_db)

    return os.path.abspath(saved_command_db), srcpath

def check_erasure(srcpath, warn):
    # Anthony : Hacking, will come back to systematically find the right libs
    libs = gather_libs(srcpath)
    libs_3v = [l for l in libs if re.match(".*\.so\.\d+\.\d+\.\d+$", l)]
    libs_2v = [l for l in libs if re.match(".*\.so\.\d+\.\d+$", l)]
    libs_1v = [l for l in libs if re.match(".*\.so\.\d+$", l)]
    if len(libs_3v) == 0 and len(libs_2v) == 0 and len(libs_1v) == 0:
        # As a last resort, try non-versioned libs
        libs_0v = [l for l in libs if re.match(".*\.so$", l)]
        if len(libs_0v) == 0:
            if warn: print("\terror: failed to build shared library for " + str(srcpath))
            return []
        else:
            libs_1v = libs_0v

    built_libs = libs_3v + libs_2v + libs_1v
    erased_libs = [l for l in built_libs if check_elf(l)]
    if warn and len(erased_libs) == 0: print("\twarning: failed to erase libs for {}".format(srcpath)) 

    return erased_libs

def build_with_make(src, command_db, env):
    # Try a re-fetch and clean build with make
    srchome = copy_src(os.path.join(working_dir, src), MAKE)
    dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ]
    srcpath = dirs[0]
    success = os.path.join(srcpath, ".petablox_success")
    if os.path.exists(success):
        print("\twarning: reuse old build result")
    else:
        print("\ttrying to build with configure/make")
        configure_env = env.copy()
        configure_env["CFLAGS"] = "-L/usr/local/lib -llzload"
        configure_env["LDFLAGS"] = "-L/usr/local/lib -llzload"
        compile_env = env.copy()
        compile_env["DUMMY_LIB_GEN"] = "ON"
        compile_env["COMPILE_COMMAND_DB"] = command_db
        if os.path.exists(os.path.join(srcpath, './configure')):
            command = ['./configure']
            if src in CONFIG_OPTS:
                command = command + CONFIG_OPTS[src]
            rc = subprocess.call(command, stdout=log, stderr=subprocess.STDOUT, cwd=srcpath, env=configure_env)
        elif os.path.exists(os.path.join(srcpath, './autogen.sh')):
            rc = subprocess.call(['./autogen.sh'], stdout=log, stderr=subprocess.STDOUT, cwd=srcpath, env=configure_env)
            rc = subprocess.call(['./configure'], stdout=log, stderr=subprocess.STDOUT, cwd=srcpath, env=configure_env)

        if os.path.exists(os.path.join(srcpath, './Makefile')):
            rc = subprocess.call(['make', '-j32'], stdout=log, stderr=subprocess.STDOUT, cwd=srcpath, env=compile_env)
        else:
            print("\twarning: Makefile not found")
            return None

    libs = check_erasure(srcpath, True)
    if len(libs) > 0:
        with open(success, 'w') as f:
            f.write("\n")
        return libs
    else:
        return None 

def build_dummy(src, command_db, env):
    print("building dummy " + str(src))
    if src in MAKE_ONLY:
        return None

    srchome = copy_src(os.path.join(working_dir, src), DPKG)
    
    dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ]

    srcpath = dirs[0]

    success = os.path.join(srcpath, ".petablox_success")
    if os.path.exists(success):
        print("\twarning: reuse old build result")
    else:
        # Start the dummy build process
        dummylib_env = env.copy()
        dummylib_env["COMPILE_COMMAND_DB"] = command_db
        dummylib_env["DUMMY_LIB_GEN"] = "ON"

        build_with_dpkg(srcpath, dummylib_env, parallel=True)
    libs = check_erasure(srcpath, True)
    if len(libs) > 0:
        with open(success, 'w') as f:
            f.write("\n")
        return libs
    else:
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

def copy_src(path, ext):
    newpath = path + ext
    try:
        shutil.copytree(path, newpath, symlinks=True)
    except FileExistsError:
        print("\twarning: {} exists".format(newpath))
        pass
    return newpath

def build_src(src, libhome):
    env = os.environ.copy()
    command_db, origpath = build_original(src, env) 
    if not command_db:
        return False

    env["CC"] = os.path.join(env["KLLVM"], "build/bin/clang")
    env["CXX"] = os.path.join(env["KLLVM"], "build/bin/clang++")

    libs = build_dummy(src, command_db, env)

    if libs is None:
        # If we didn't find libs with __get in the ELF files, we have
        # to try ad-hoc rules
        if os.path.exists(os.path.join(origpath, "configure")) \
        or os.path.exists(os.path.join(origpath, "autogen.sh")) \
        or os.path.exists(os.path.join(origpath, "Makefile")):
            libs = build_with_make(src, command_db, env)
        if libs is None:
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

    stat = open(os.path.join(working_dir, pkg_name + '.stat'), "w")
    stat.write("package name, build\n")

    for s in srcs:
        rc = build_src(s, libhome)
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
log = open("build.log", "w")
deps=read_dependency_list(deplist)
srcs=download_srcs(deps)

pkgname = deplist.split('/')[-1]

build_srcs(srcs, pkgname)

log.close()

