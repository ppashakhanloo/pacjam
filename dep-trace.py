#!/usr/bin/env python3

import subprocess
import os.path
import sys
import time


from optparse import OptionParser

def read_dependency_list(name):
    deps = {}
    with open(name, 'r') as f:
        for d in f.read().splitlines():
            deps[d] = True
    return deps

def sample(pid,libs):
    lsof = subprocess.Popen(['lsof', '-p', pid], stdout=subprocess.PIPE)

    try:
        out = subprocess.check_output(['grep','lib'], stdin=lsof.stdout)
    except:
        return

    for l in out.splitlines():
        fulllib = str(l.split()[-1],'utf-8')
        libname = fulllib.split('/')[-1]
        
        libs[libname] = fulllib


def monitor_pid(pid,timeout,rate):
    print("monitoring process " + pid)
    target = timeout / 1000.0
    freq = rate / 1000.0
    elapsed=0.0

    libs = {}
    while elapsed < target:
        sample(pid,libs)
        time.sleep(freq)
        elapsed += freq

    return libs


def monitor_process(process,rate):
    print("monitoring process " + str(process.pid))
    freq = rate / 1000.0

    libs = {}
    process.poll()
    while process.returncode is None:
        sample(str(process.pid),libs)
        time.sleep(freq)
        process.poll()

    return libs

def search_deps(libs,deps):
    print('Package has ' + str(len(deps)) + ' transitive dependencies')
    for d in deps:
        print('\t' + d)
    print('Process used ' + str(len(libs)) + ' libraries')
    for l,fullname in libs.items():
        print('\t' + str(fullname))

    print('Attempting to match...')

    notused = deps.copy()
    used = {}

    for l in libs:
        # We'll just look for 'libX' match for now
        if 'lib' not in l:
            continue
        idx = l.find(".so")
        if idx < 1:
            continue
        libby = l[:idx]
        libby = libby.split('-')[0]

        found = None
        
        for d in notused:
            if libby in d:
                found = d
                break

        if found is not None:
            notused.pop(found)
            used[found] = l

    print('Matched ' + str(len(used)) + ' dependencies')
    for d,l in used.items():
        print('\t' + str(d) + ' ==> ' + str(l))

    print('Possibly ' + str(len(notused)) + ' unused dependencies')
    for d in notused:
        print('\t' + str(d))
    

def execute(procstr, rate):
    print("executing " + procstr)
    p = procstr.replace("'","").split()
    proc = subprocess.Popen(p)
    return monitor_process(proc,rate)

usage = "usage: %prog [options] dependency-list"
parser = OptionParser(usage=usage)
parser.add_option('-p', '--pid', dest='pid', help='monitor running process PID', metavar='PID')
parser.add_option('-e', '--execute', dest='execute', help='start and monitor PROGRAM', metavar='PROGRAM')
parser.add_option('-t', '--timeout', dest='timeout', default=1000, help='monitor for TIME ms', metavar='TIME')
parser.add_option('-r', '--rate', dest='rate', default=10, help='sample every TIME ms', metavar='TIME')

(options, args) = parser.parse_args()

if (len(args) < 1 or options.pid is None and options.execute is None) or (options.pid is not None and options.execute is not None):
    print("error: must supply pid OR execute")
    parser.print_usage()
    sys.exit(1)

deps=read_dependency_list(args[0])
   
if options.pid is not None:
    libs = monitor_pid(options.pid,options.timeout,options.rate)
    search_deps(libs,deps)
else:
    libs = execute(options.execute,options.rate)
    search_deps(libs,deps)







