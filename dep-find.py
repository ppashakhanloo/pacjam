#!/usr/bin/env python3

import json
import os.path
import sys
from os import walk
from typing import List, Tuple
import logging

from optparse import OptionParser 

log = logging.getLogger()
log.setLevel(logging.INFO)


def load(filename: str) -> Tuple[dict, bool]:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            deps = json.load(f)

            return deps, False

    return {}, True


def save(deps: dict, filename: str) -> None:
    with open(filename, 'w') as f:
        json.dump(deps, f, indent=2)


def get_package_file(distro: str, category: str, arch: str) -> str:
    try:
        base_dir, _, file_list = next(walk('/var/lib/apt/lists'))
    except StopIteration:
        logging.error('Cannot access: /var/lib/apt/lists')
        sys.exit(-1)

    suffix: str = f'_{distro}_{category}_binary-{arch}_Packages'

    for file in file_list:
        if file.endswith(suffix):
            # make sure debian repo, not 3rd-party
            if file.find("fir01.seas.upenn.edu") != -1:
                return f'{base_dir}/{file}'

    return ''


def parse_package_list(packages_str: str) -> List[str]:
    packages = []
    for package_info in packages_str.split(','):
        package_name = package_info.split()[0].strip()
        packages.append(package_name)

    log.debug(f'Dep-packages: {packages}')
    return packages


def fetch(deps: dict, distro: str, category: str, arch: str) -> dict:
    package_file = get_package_file(distro, category, arch)
    log.info(f'Building deps: {package_file}')

    if len(package_file) == 0:
        log.error("Matched 'Packages' file not found. Please run 'apt-get update', then retry.")
        sys.exit(-1)

    with open(package_file, 'rt', errors='replace') as infile:
        line_no: int = 0
        current_package: str = ''
        for line in infile:
            line_no += 1
            tokens = line.strip().split()

            if len(tokens) == 0:
                # end of package
                current_package = ''
                continue

            category: str = tokens[0].strip()

            if category == 'Package:':
                if current_package != '':
                    log.error(f"Something wrong in 'Packages'' file format. (Line={line_no})")
                    sys.exit(-1)

                current_package = tokens[1].strip()
                if current_package in deps:
                    log.error(f'Duplicated package name: {current_package}')
                    sys.exit(-1)

                deps[current_package] = []
            elif category in ['Depends:', 'Recommends:', 'Pre-Depends:']:
                if current_package == '':
                    log.error(f'Depends for empty package. (Line={line_no})')
                    sys.exit(-1)

                deps[current_package].extend(parse_package_list(' '.join(tokens[1:])))

    return deps


def fixpt(deps, works, results):
    if len(works) == 0:
        return results
    w = works.pop()
    try:
        directs = deps[w]
    except:
        directs = set()
    for d in directs:
        if d in results:
            continue
        else:
            works.update(directs)
            results.update(directs)
    return fixpt(deps, works, results)


def search(name, deps):
    works = set()
    works.add(name)
    results = set()
    trans_deps = fixpt(deps, works, results)
    with open(name + '.dep', 'w') as f:
        for p in sorted(trans_deps):
            f.write('{}\n'.format(p))


def stats(deps, g, trans):
    size_table = list(map(lambda x: (x, len(deps[x])), deps))
    size_table.sort(key=lambda x: x[1], reverse=True)

    trans_size_table = []
    v_prop = g.vertex_properties['info']
    for v in trans.vertices():
        trans_size_table.append((v_prop[v]['label'], len(list(v.out_edges()))))
    trans_size_table.sort(key=lambda x: x[1], reverse=True)

    with open('direct.txt', 'w') as f:
        counter = 1
        f.write('{}, {}, {}\n'.format('Rank', 'name', 'size'))
        for name, size in size_table:
            f.write('{}, {}, {}\n'.format(counter, name, size))
            counter += 1
    with open('transitive.txt', 'w') as f:
        f.write('# Transitive Dependencies\n')
        counter = 1
        f.write('{}, {}, {}\n'.format('Rank', 'name', 'size'))
        for name, size in trans_size_table:
            f.write('{}, {}, {}\n'.format(counter, name, size))
            counter += 1


parser = OptionParser()
parser.add_option('-p', '--package', dest='package', help='build a dependency list for PACKAGE', metavar='PACKAGE')
parser.add_option('-f', '--file', default='deps.json',
                  help='Name of deps-file. [default: %default]')
parser.add_option('-r', '--rebuild', action='store_true', default=False,
                  help='Rebuild deps-file. [default: %default]')
parser.add_option('-d', '--distro', default='buster',
                  help='Linux distribution (required only for building deps-file). [default: %default]')
parser.add_option('-c', '--category', default='main',
                  help='Package category (required only for building deps-file).  [default: %default]')
parser.add_option('-a', '--arch', default='amd64',
                  help='Architecture (required only for building deps-file). [default: %default]')

(options, args) = parser.parse_args()

deps, need_init = load(options.file)

# reset if rebuild is True
if options.rebuild:
    deps = {}
    need_init = True

if need_init:
    deps = fetch(deps, options.distro, options.category, options.arch)
    save(deps, options.file)

if options.package is not None:
    search(options.package, deps)
