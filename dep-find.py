#!/usr/bin/env python3

import json
import os.path
import graph_tool.all
import sys
from os import walk
from typing import List, Tuple
import logging

from optparse import OptionParser 

log = logging.getLogger()
log.setLevel(logging.INFO)


def get_vertex(g, name2idx, v_prop, name):
    if name in name2idx:
        return name2idx[name]
    v = g.add_vertex()
    v_prop[v] = {'label': name}
    idx = g.vertex_index[v]
    name2idx[name] = idx
    return idx


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

    with open(package_file, 'rt') as infile:
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


def build(deps):
    g = graph_tool.Graph()
    name2idx = {}
    v_prop = g.new_vertex_property('object')
    total = len(deps)
    counter = 0

    for name, depends in deps.items():
        counter += 1
        print('[{}/{}] Building {}'.format(counter, total, name))
        src = get_vertex(g, name2idx, v_prop, name)
        edges = []
        for dep_name in depends:
            dst = get_vertex(g, name2idx, v_prop, dep_name)
            edges.append((src, dst))
        g.add_edge_list(edges)

    g.vertex_properties['info'] = v_prop
    return g, name2idx


def transitive_closure(g):
    transitive = graph_tool.topology.transitive_closure(g)
    return transitive


def draw(g, output):
    v_prop = g.vertex_properties['info']
    #v_shape = g.vertex_properties['shape']
    #v_color = g.vertex_properties['color']
    #vprops = {'shape': v_shape}
    graph_tool.graphviz_draw(
        g,
        #    vcolor=v_color,
        #    vprops=vprops,
        size=(30, 30),
        overlap=False,
        output=output)


def print_node_id(g, output):
    v_prop = g.vertex_properties['info']

    with open(output, 'w') as f:
        for v in g.vertices():
            f.write('{}: {}\n'.format(v, v_prop[v]['label']))

def search(name, name2idx, g, trans):
    v_prop = g.vertex_properties['info']
    print(v_prop)
    idx = name2idx[name]
    index = trans.vertex_index.copy()
    dp = graph_tool.util.find_vertex(trans,index,idx)[0]

    with open(name + '.dep', 'w') as f:
        for w in dp.out_neighbors():
            if '<' not in v_prop[w]['label']:
                f.write('{}\n'.format(v_prop[w]['label']))


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

g, name2idx = build(deps)
transitive = transitive_closure(g)

if need_init:
    stats(deps, g, transitive)

if options.package is not None:
    search(options.package, name2idx, g, transitive)

#draw(g, 'output.svg')
#print_node_id(g, 'labels.txt')
