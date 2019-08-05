#!/usr/bin/env python3

import subprocess
import os.path
import sys
import glob

from optparse import OptionParser 

import json

working_dir = ""

# Really just for tracking a bit more about a symbol stored in our table
class Symbol:
    name = ""
    libs = []
    metas = []

    def __init__(self,name,libs,metas):
        self.name = name
        self.libs = libs
        self.metas = metas

class Meta:
    package_name = ""
    package_deb = ""
    has_symbols = False
    shared_libs = []

    def __init__(self,package_name,package_deb,has_symbols,shared_libs):
        self.package_name = package_name
        self.package_deb = package_deb
        self.has_symbols = has_symbols
        self.shared_libs = shared_libs

    def json_state(self):
        return self.__dict__

    def as_meta(dct):
        return Meta(dct["package_name"],dct["package_deb"],dct["has_symbols"],dct["shared_libs"])
    

class MetaEncoder(json.JSONEncoder):

    def default(self,o):
        if isinstance(o, Meta):
            return o.json_state()
        else:
            return json.JSONEncoder.default(self, o)


def read_dependency_list(name):
    deps = {}
    with open(name, 'r') as f:
        for d in f.read().splitlines():
            deps[d] = True
    return deps

def download_deps(deps):
    debs = {}

    for d in deps:
        print('fetching ' + d)
        try:
            out = subprocess.check_output(['apt-get', 'download', d])
            deb = glob.glob(d + '*.deb')[0]
            debs[d] = deb
            os.rename(deb, working_dir + '/' + deb)
        except:
            print("No package found for " + d)

    return debs

def extract_debs(debs):
    # Create some metadata about our little repository
    meta = []

    home = os.getcwd()

    for dep,deb in debs.items():
        debhome = os.path.join(working_dir,dep)
        os.mkdir(debhome)
        os.rename(os.path.join(working_dir,deb),os.path.join(debhome,deb))
        os.chdir(debhome)
        out = subprocess.check_output(['ar', '-xv', deb])
        out = subprocess.check_output(['tar', 'xf', 'control.tar.xz'])

        # Test for symbol file
        has_sym = os.path.exists('symbols')

        os.chdir(home) 
        meta.append(Meta(dep, deb, has_sym, []))
        save_meta()


def parse_symbols(meta,symbols):
    # We'll point every symbol to its metadata for now
    # Build a true repo later

    with open(os.path.join(working_dir, meta.package_name, "symbols")) as f:
        current_lib = ""
        for l in f.readlines():
            toks = l.split()
            if toks[-1] == "#MINVER#":
                current_lib = toks[0]
                meta.shared_libs.append(current_lib)
            elif toks[0] == "|":
                pass
            else:
                name = toks[0].split("@")[0]
                if name in symbols:
                    # Possible conflict (really only an issue between packages for now)
                    symbols[name].libs.append(current_lib)
                    symbols[name].metas.append(meta)
                else:    
                    symbols[name] = Symbol(name,[current_lib],[meta])
        

def load_meta():
    with open(os.path.join(working_dir, 'meta.json'), 'r') as f:
        meta = json.load(f, object_hook=Meta.as_meta) 
    return meta        

def save_meta():
    with open(os.path.join(working_dir,'meta.json'), 'w') as f:
        json.dump(meta, f, indent=2, cls=MetaEncoder)

def load_symbols(meta):
    symbols = {}

    for m in meta:
        if m.has_symbols:
            parse_symbols(m, symbols)

    return symbols

def load_trace(name):
    calls = []
    if os.path.exists(name):
        with open(name, 'r') as f:
            for line in f:
                j = json.loads(line)
                if j['inst'] == 'call':
                    calls.append(j)
    else:
        return {}

    return calls

def check_deps(meta,symbols,calls):
    track = {}
    for m in meta:
        track[m.package_name] = False

    for c in calls:
        if c["indirect"]:
            continue
        fname = c["fnptr"][1:]
        sym = symbols.get(fname)
        if sym is not None:
            track[sym.metas[0].package_name] = True
        
    # Just for nice output
    used = []
    notused = []

    for d,t in track.items():
        if t:
            used.append(d)
        else:
            notused.append(d)

    print('Package has ' + str(len(track)) + ' tracked dependencies')
    print('Using ' + str(len(used)) + ':')
    for d in used:
        print('\t' + d)

    print('Not using ' + str(len(notused)) + ':')
    for d in notused:
        print('\t' + d)


usage = "usage: %prog [options] dependency-list"
parser = OptionParser(usage=usage)
parser.add_option('-d', '--dir', dest='working_dir', default='symbol-out', help='use DIR as working output directory', metavar='DIR')
parser.add_option('-t', '--trace', dest='trace', help='load trace file DIR', metavar='TRACE')
parser.add_option('-l', '--load', action='store_true', help='jump straight to loading the repository symbols')

(options, args) = parser.parse_args()

working_dir = options.working_dir

if len(args) < 1:
    print("error: must supply dependency-list")
    parser.print_usage()
    sys.exit(1)

if not options.load:
    deps=read_dependency_list(args[0])
    debs=download_deps(deps)
    extract_debs(debs)

meta = load_meta()
symbols = load_symbols(meta)
save_meta()

if options.trace is not None:
    calls = load_trace(options.trace)
    check_deps(meta,symbols,calls) 
   








