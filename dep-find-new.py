#!/usr/bin/python3

import subprocess
import json
import os.path

from optparse import OptionParser 


def load(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            db = json.load(f)
        return db, False
    else:
        return {}, True


def save(filename, deps):
    with open(filename, 'w') as f:
        json.dump(deps, f, indent=2)


def fetch(filename, deps):
    lst = subprocess.check_output(['apt-cache', 'search', '.']).decode()
    counter = 0
    lst = lst.split('\n')
    total = len(lst)
    counter = 0
    for pkg in lst:
        name = pkg.split(' ')[0]
        counter += 1
        print('[{}/{}] Fetching {}'.format(counter, total, name))
        if name in deps:
            continue
        if name == '':
            continue
        depends = subprocess.check_output([
            'apt-cache', 'depends', '--no-suggests', '--no-breaks',
            '--no-conflicts', name
        ]).decode()
        dep_list = []

        for dep in [dep for dep in depends.split('\n') if 'Depends:' in dep or 'Recommends:' in dep]:
            dep_name = dep.split(':')[1].strip()
            dep_list.append(dep_name)
        deps[name] = dep_list

        if counter % 1000 == 0:
            save(filename, deps)
    save(filename, deps)
    return deps


def fixpt(db, works, deps):
    if len(works) == 0:
        return deps
    w = works.pop()
    try:
        directs = db[w]
    except:
        directs = set()
    for d in directs:
        if d in deps:
            continue
        else:
            works.update(directs)
            deps.update(directs)
    return fixpt(works, deps)


parser = OptionParser()
parser.add_option('-p', '--package', dest='package', help='build a dependency list for PACKAGE', metavar='PACKAGE')
parser.add_option('-o', '--output', dest='output', help='output json file', metavar='OUPTUT')

(options, args) = parser.parse_args()

db, need_init = load(options.output)
if need_init:
    db = fetch(options.output, db)

works = set()
works.add(options.package)
results = set()
results.add(options.package)
trans_deps = fixpt(db, works, results)

for l in trans_deps:
    if '<' not in l:
        print(l)
