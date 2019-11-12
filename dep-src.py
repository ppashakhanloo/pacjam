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

EXCLUDES=["libc6", "libgcc1", "gcc-8-base", "<debconf-2.0>", "debconf", "libselinux1", "libzstd1", "libstdc++6", "dpkg", "tar", "perl-base", "install-info"]

CONFIG_OPTS={ "libtinfo6": ["--with-shared", "--with-termlib"], "libncurses6": ["--with-shared"], "libncursesw6": ["--with-shared"],
              "libopus0": ["--disable-maintainer-mode"], "libprotobuf-lite17": ["--disable-maintainer-mode", "--disable-dependency-tracking"] }

MAKE_ONLY=["libbluray2", "libprotobuf-lite17"]

ORIGINAL=".original"
DPKG=".dpkg"
MAKE=".make"
VARARG=".vararg"

options = {}

LZLOAD_SYMBOL="__get_lib_name"
VARARG_SYMBOL="__dummy__va"

def dump_vararg_symbols(lib, f):
    soname = soname_lib(lib)
    symbols = readelf_grepped(lib, VARARG_SYMBOL)
    if symbols is None:
        print("\twarning: expected vararg symbols for {} but found none".format(lib))
        return

    for s in symbols:
        f.write("{} {}\n".format(s,soname))

def generate_vararg_symbols(libs):
    with open(os.path.join(options.working_dir,'symbols.txt'), 'w') as f:
        for l in libs:
            dump_vararg_symbols(l,f)

def gather_libs(path):
    out = subprocess.run(['find',path, '-name', 'lib*.so*'], stdout=subprocess.PIPE)
    libs = []
    for l in out.stdout.splitlines():
        libs.append(l.decode('utf-8'))
    return libs

def gather_lib(path, name):
    out = subprocess.run(['find', path, '-name', name], stdout=subprocess.PIPE)
    libs = []
    for l in out.stdout.splitlines():
        libs.append(l.decode('utf-8'))
    return libs


def readelf_grepped(path, pattern):
    readelf = subprocess.Popen(['readelf', '-Ws', path], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
    out = subprocess.run(['grep',pattern], stdout=subprocess.PIPE, stdin=readelf.stdout)

    if out.stdout is None:
        return None
    
    symbols = []
    out = out.stdout.decode("utf-8")

    for l in out.splitlines():
        toks = l.split()
        symbols.append(toks[-1])

    return symbols 

def check_elf(path, symbol):
    readelf = subprocess.Popen(['readelf', '-Ws', path], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
    out = subprocess.run(['grep',symbol], stdout=subprocess.PIPE, stdin=readelf.stdout)
    return len(out.stdout) > 0

def get_soname(path):
    objdump = subprocess.Popen(['objdump', '-p', path], stdout=subprocess.PIPE)
    out = subprocess.run(['grep','SONAME'], stdout=subprocess.PIPE, stdin=objdump.stdout)
    if len(out.stdout) == 0:
        return None
    return out.stdout.strip().split()[-1] 

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
        srchome = os.path.join(options.working_dir,dep)
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

def try_build_dep(src):
    rc = subprocess.call(['apt-get', 'build-dep', '-y', src], stdout=log, stderr=subprocess.STDOUT)
    if rc != 0:
        rc = subprocess.call(['dpkg', '--configure', '-a'], stdout=log, stderr=subprocess.STDOUT)
        rc = subprocess.call(['apt-get', 'build-dep', '-y', src], stdout=log, stderr=subprocess.STDOUT)
    return rc

def build_original(src, env):
    print("building original " + str(src))

    srchome = copy_src(os.path.join(options.working_dir, src), ORIGINAL, options.force)

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
    reuse_saved_db = os.path.exists(saved_command_db)

    if not reuse_saved_db or options.force:
        # Build the package normally first to get a compile_command.json
        build_with_dpkg(srcpath, env)

        # Check for compile_command.json, and then move to tmp file so the next build doesn't
        # overwrite it 
        command_db = os.path.join(srcpath, "compile_commands.json")

        if not os.path.exists(command_db):
            print("\terror: failed to generate compile_commands.json for {}, skipping...".format(src))
            return None, None

        if not reuse_saved_db:
            os.makedirs(os.path.dirname(saved_command_db), exist_ok=True)
            shutil.copy(command_db, saved_command_db)

    if reuse_saved_db:
        print("\tinfo: reusing saved compilation db")

    return os.path.abspath(saved_command_db), srcpath

def build_vararg(src, env):
    srchome = copy_src(os.path.join(options.working_dir, src), VARARG, options.force)
    dirs = [f.path for f in os.scandir(srchome) if f.is_dir() ] 
    srcpath = dirs[0]

    if len(dirs) > 1:
        print("error: multiple source directories for package: {}".format(src))
        return None
    if len(dirs) == 0:
        print("error: no source directories for package: {}".format(src))
        return None 

    vararg_env = env.copy()
    vararg_env["DUMMY_LIB_GEN"] = "ON"

    vararg_libs = gather_libs(srcpath)
    if len(vararg_libs) > 0:
        return srcpath

    build_with_dpkg(srcpath, vararg_env)

    return srcpath

def check_libs(srcpath, ref_libs, dummy_libs):
    common = srcpath.split("/")[-1]
    rlibs = [l.split(common)[-1] for l in ref_libs]
    dlibs = [l.split(common)[-1] for l in dummy_libs]

    rset = set(rlibs)
    dset = set(dlibs)
    diff = rset - dset

    if len(diff) != 0 and options.verbose:
        print("\twarning: original and dummy libraries different")

        print("\t== Reference ==")
        for s in ref_libs:
            print("\t" + s)

        print("\t== Dummy ==")
        for s in dummy_libs:
            print("\t" + s)

def check_erasure(libs, warn):
    erased_libs = [l for l in libs if not os.path.islink(l) and check_elf(l, LZLOAD_SYMBOL)]
    if warn and len(erased_libs) == 0: print("\twarning: failed to erase libs")
    return erased_libs

def check_vararg(libs):
    vararg_libs = [l for l in libs  if check_elf(l, VARARG_SYMBOL)]
    return vararg_libs

def build_with_make(src, command_db, env, origpath):
    # Try a re-fetch and clean build with make
    srchome = copy_src(os.path.join(options.working_dir, src), MAKE, False)
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

    dummy_libs = gather_libs(srcpath)
    libs = check_erasure(dummy_libs, True)

    if len(libs) > 0:
        with open(success, 'w') as f:
            f.write("\n")
        return libs
    else:
        return None 

def find_unpacked_srcdir(path):
    dirs = [f.path for f in os.scandir(path) if f.is_dir() ]
    return dirs[0] 

def build_dummy(src, command_db, env, origpath):
    print("building dummy " + str(src))
    if src in MAKE_ONLY:
        return None

    srchome = copy_src(os.path.join(options.working_dir, src), DPKG, False)
    srcpath = find_unpacked_srcdir(srchome)

    success = os.path.join(srcpath, ".petablox_success")
    if os.path.exists(success):
        print("\twarning: reuse old build result")
    else:
        # Start the dummy build process
        dummylib_env = env.copy()
        dummylib_env["COMPILE_COMMAND_DB"] = command_db
        dummylib_env["DUMMY_LIB_GEN"] = "ON"

        build_with_dpkg(srcpath, dummylib_env, parallel=True)

    ref_libs = gather_libs(origpath)
    dummy_libs = gather_libs(srcpath)
    check_libs(srcpath, ref_libs, dummy_libs) 

    libs = check_erasure(dummy_libs, True)

    if len(libs) > 0:
        with open(success, 'w') as f:
            f.write("\n")
        return libs
    else:
        return None 
    
def copy_src(path, ext, force):
    newpath = path + ext
    if os.path.exists(newpath) and force:
        shutil.rmtree(newpath)
    try:
        shutil.copytree(path, newpath, symlinks=True)
    except FileExistsError:
        print("\twarning: {} exists".format(newpath))
        pass
    return newpath 

def trim_libname(libpath):
    return libpath.split("/")[-1]

def soname_lib(libpath):
    soname = get_soname(libpath)
    if soname is not None:
        soname = soname.decode("utf-8")
    else:
        soname = trim_libname(libpath)
    return soname


# Anthony : Refactor this functionality out. 
def scrape_lib(src, libhome):
    dpkg_home = os.path.join(options.working_dir, src) + DPKG
    make_home = os.path.join(options.working_dir, src) + MAKE

    libs = check_erasure(gather_libs(find_unpacked_srcdir(dpkg_home)), False)
    if len(libs) == 0: 
        libs = check_erasure(gather_libs(find_unpacked_srcdir(make_home)), False)
    
    if len(libs) == 0:
        print("\twarning: no libs built")
        return None

    # If it follows the .libs pattern, filter for those, else we just leave as is
    deblibs = [l for l in libs if ".lib" in l]
    if len(deblibs) > 0:
        libs = deblibs

    for l in libs:
        name = trim_libname(l)
        soname = soname_lib(l)
        
        shutil.copy(l, libhome)
        # Create "version"
        path = os.path.join(libhome,soname)
        shutil.copy(l, path)

        print("\tbuilt {} => {}".format(name, soname)) 

    return libs

def scrape_libs(srcs, pkg_name):
    libhome = os.path.join(options.working_dir, "lib")
    if not os.path.exists(libhome):
        os.mkdir(libhome)
    for s in srcs:
        scrape_lib(s, libhome)

def build_src(src, libhome, modhome):
    env = os.environ.copy()
    command_db, origpath = build_original(src, env) 
    if not command_db:
        return False

    env["CC"] = os.path.join(env["KLLVM"], "build/bin/clang")
    env["CXX"] = os.path.join(env["KLLVM"], "build/bin/clang++")

    libs = build_dummy(src, command_db, env, origpath)

    if libs is None:
        # If we didn't find libs with __get in the ELF files, we have
        # to try ad-hoc rules
        if os.path.exists(os.path.join(origpath, "configure")) \
        or os.path.exists(os.path.join(origpath, "autogen.sh")) \
        or os.path.exists(os.path.join(origpath, "Makefile")):
            libs = build_with_make(src, command_db, env, origpath)
        if libs is None:
            return False

    # Anthony : I don't like how this scraping is essentially recomputed
    libs = scrape_lib(src, libhome)

    vararg_libs = check_vararg(libs)
    if len(vararg_libs) > 0:
        generate_vararg_symbols(vararg_libs) 
        varargpath = build_vararg(src, env)
        for l in vararg_libs:
            name = trim_libname(l)
            canidate_libs = gather_lib(varargpath, name)
            if len(canidate_libs) == 0:
                print("\twarning: found no candidate vararg libs for {}".format(l))
                continue
            if len(canidate_libs) > 1:
                print("\twarning: multiple candidate vararg libs for {}".format(name))

            vl = canidate_libs[0]
            print("\tinfo: using candidate for {}".format(vl))

            soname = soname_lib(vl)
            
            shutil.copy(vl, modhome)
            # Create "version"
            path = os.path.join(modhome,soname)
            shutil.copy(vl, path)

            print("\tvararg {} => {}".format(name, soname)) 

    return True

def build_srcs(srcs, pkg_name):
    libhome = os.path.join(options.working_dir, "lib")
    if not os.path.exists(libhome):
        os.mkdir(libhome)
    modhome = os.path.join(options.working_dir, "mod-lib")
    if not os.path.exists(modhome):
        os.mkdir(modhome)

    env = os.environ.copy()

    if not env["KLLVM"]:
        print("error: Set KLLVM to point to our modified LLVM installation")
        return

    stat = open(os.path.join(options.working_dir, pkg_name + '.stat'), "w")
    stat.write("package name, build\n")

    for s in srcs:
        rc = build_src(s, libhome, modhome)
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
parser.add_option('-f', '--force', dest='force', action='store_true', help='force rebuild of original packages', metavar='DIR')
parser.add_option('-s', '--scrape', dest='scrape', action='store_true', help='scrape libraries of built packages', metavar='DIR')
parser.add_option('-v', '--verbose', dest='verbose', action='store_true', help='verbose output', metavar='DIR')

(options, args) = parser.parse_args()

if len(args) < 1:
    print("error: must supply dependency-list")
    parser.print_usage()
    sys.exit(1)

deplist = args[0]
log = open("build.log", "w")
deps=read_dependency_list(deplist)
srcs=download_srcs(deps)

pkgname = deplist.split('/')[-1]

if options.scrape:
    scrape_libs(srcs, pkgname)
else: 
    build_srcs(srcs, pkgname)

log.close()

