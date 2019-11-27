#!/usr/bin/python3

import json
import sys

with open('deps.jessie.json') as f:
    db = json.load(f)


def fixpt(works, deps):
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

target = sys.argv[1]
works = set()
works.add(target)
deps = set()
deps.add(target)
trans_deps = fixpt(works, deps)

for l in trans_deps:
    if '<' not in l:
        print(l)
