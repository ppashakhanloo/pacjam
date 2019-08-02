#!/usr/bin/env python3

import subprocess
import json
import os.path
import sys
import glob

from optparse import OptionParser 

def read_dependency_list(name):
    deps = {}
    with open(name, 'r') as f:
        for d in f.read().splitlines():
            deps[d] = True
    return deps

def download_deps(deps, outdir):
    debs = {}

    for d in deps:
        print('fetching ' + d)
        try:
            out = subprocess.check_output(['apt-get', 'download', d])
            deb = glob.glob(d + '*.deb')[0]
            debs[d] = deb
            os.rename(deb, outdir + '/' + deb)
        except:
            print("No package found for " + d)

    return debs

def extract_debs(debs,outdir):
    # Create some metadata about our little repository
    meta = []

    home = os.getcwd()

    for dep,deb in debs.items():
        debhome = os.path.join(outdir,dep)
        os.mkdir(debhome)
        os.rename(os.path.join(outdir,deb),os.path.join(debhome,deb))
        os.chdir(debhome)
        out = subprocess.check_output(['ar', '-xv', deb])
        out = subprocess.check_output(['tar', 'xf', 'control.tar.xz'])

        # Test for symbol file
        has_sym = os.path.exists('symbols')

        os.chdir(home) 
        meta.append({"package-name": dep, "package-deb": deb, "has-symbols":has_sym})

    with open(os.path.join(outdir,'meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)

def parse_symbols(meta,outdir, symbols):
    # We'll point every symbol to its metadata for now
    # Build a true repo later

    with open(os.path.join(outdir, meta["package-name"], "symbols")) as f:
        current_dep = ""
        for l in f.readlines():
            toks = l.split()
            if toks[-1] == "#MINVER#":
                current_dep = toks[0]
            elif toks[0] == "|":
                pass
            else:
                sym = toks[0].split("@")[0]
                if sym in symbols:
                    print("Warning: conflict for " + sym)
                symbols[sym] = meta
        

def load_meta(outdir):
    with open(os.path.join(outdir, 'meta.json'), 'r') as f:
        meta = json.load(f) 
    return meta        

def load_symbols(meta,outdir):
    symbols = {}

    for m in meta:
        if m["has-symbols"]:
            parse_symbols(m, outdir, symbols)

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
        track[m["package-name"]] = False

    for c in calls:
        if c["indirect"]:
            continue
        fname = c["fnptr"][1:]
        if fname in symbols:
            track[symbols[fname]["package-name"]] = True
        
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
parser.add_option('-d', '--dir', dest='outdir', default='symbol-out', help='use DIR as working output directory', metavar='DIR')
parser.add_option('-t', '--trace', dest='trace', help='load trace file DIR', metavar='TRACE')
parser.add_option('-l', '--load', action='store_true', help='jump straight to loading the repository symbols')

(options, args) = parser.parse_args()

if len(args) < 1:
    print("error: must supply dependency-list")
    parser.print_usage()
    sys.exit(1)

if not options.load:
    deps=read_dependency_list(args[0])
    debs=download_deps(deps,options.outdir)
    extract_debs(debs,options.outdir)

meta = load_meta(options.outdir)
symbols = load_symbols(meta,options.outdir)

if options.trace is not None:
    calls = load_trace(options.trace)
    check_deps(meta,symbols,calls) 
   








