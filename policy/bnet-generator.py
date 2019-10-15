#!/usr/bin/python3

import json
import os
import graph_tool.all
import math
import time
import logging

from argparse import ArgumentParser

REPO_HOME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEPS_PATH = os.path.join(REPO_HOME, 'deps.json')
POPCON_PATH = os.path.join(REPO_HOME, 'popcon-data')

logging.basicConfig(
    filename='bnet-generator.log',
    filemode='w',
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")


def get_vertex(g, name2idx, v_prop, name):
    if name in name2idx:
        return name2idx[name]
    v = g.add_vertex()
    v_prop[v] = {'label': name}
    idx = g.vertex_index[v]
    name2idx[name] = idx
    return idx


def build(deps):
    g = graph_tool.Graph()
    name2idx = {}
    v_prop = g.new_vertex_property('object')

    counter = 0

    for name, depends in deps.items():
        counter += 1
        src = get_vertex(g, name2idx, v_prop, name)
        edges = []
        for dep_name in depends:
            dst = get_vertex(g, name2idx, v_prop, dep_name)
            edges.append((src, dst))
        g.add_edge_list(edges)

    g.vertex_properties['info'] = v_prop
    return g, name2idx


def store_vertex_dict(g):
    with open('{}/{}/bnet-dict.txt'.format(REPO_HOME, 'policy'), 'w') as f:
        count = 0
        for pkg in g.vertices():
            f.write('{}: {}\n'.format(
                count, g.vertex_properties['info'][pkg]['label']))
            count += 1


def get_bin(x, n):
    return format(x, 'b').zfill(n)


def get_daily_info(pkg):
    filename = '{}/{}.daily.json'.format(POPCON_PATH, pkg)
    if not os.path.exists(filename):
        return None
    with open(filename) as f:
        data = json.load(f)
    return data


def invalid_date(names, daily_info_list, date):
    for i in range(0, len(names)):
        if date not in daily_info_list[i][names[i]]:
            return True
    return False


def match(daily_info, bit):
    return bool(int(bit)) == daily_info['binary']


def compute_conditional_probability(names, daily_info_list, bin_vector):
    assert (len(names) == len(daily_info_list)
            and len(names) == len(bin_vector))
    target = daily_info_list[-1][names[-1]]
    hypothesis_date = 0
    conclusion_date = 0
    for date in target:
        # if there exists a package not installed at the time
        if invalid_date(names, daily_info_list, date):
            continue
        # count the number of days where the hypothesis matches
        hypothesis_hit = True
        for i in range(0, len(names) - 1):
            hypothesis_hit = hypothesis_hit and match(
                daily_info_list[i][names[i]][date], bin_vector[i])
        if hypothesis_hit:
            hypothesis_date += 1

        # count the number of days where the conclusion matches
        i = len(names) - 1
        conclusion_hit = match(daily_info_list[i][names[i]][date],
                               bin_vector[i])
        if hypothesis_hit and conclusion_hit:
            conclusion_date += 1
    if hypothesis_date == 0:
        return 0
    else:
        return float(conclusion_date) / float(hypothesis_date)


# https://staff.fnwi.uva.nl/j.m.mooij/libDAI/doc/fileformats.html
def print_factor(name2idx, nodes, factor_table, f):
    # number of nodes
    f.write(str(len(nodes)) + "\n")
    # node ids
    s = ""
    for node in nodes:
        s = s + str(name2idx[node]) + " "
    f.write(s + "\n")
    # arity
    s = ""
    for node in nodes:
        s = s + "2 "
    f.write(s + "\n")
    count = 0
    for i in range(0, len(factor_table)):
        if factor_table[i] == 0:
            continue
        count += 1
    f.write("{}\n".format(count))
    for i in range(0, len(factor_table)):
        if factor_table[i] == 0:
            continue
        f.write("{} {}\n".format(i, factor_table[i]))
    f.write('\n')


def generate_factor_graph(args, g, name2idx, reachable_nodes):
    store_vertex_dict(g)
    vp = g.vertex_properties['info']

    total = len(reachable_nodes)
    count = 0
    result = {}
    result['skipped'] = 0
    factors = []
    for pkg in reachable_nodes:
        count += 1
        name = vp[pkg]['label']
        print('[{}/{}] Processing nodes...'.format(count, total), end='\r')
        # TODO: handle properly
        reachable_pred = [
            p.source() for p in pkg.in_edges() if p.source() in reachable_nodes
        ]
        logging.info('{} / {} are reachable pred'.format(
            len(reachable_pred), pkg.in_degree()))
        if pkg.in_degree() > args.max_pred:
            result['skipped'] += 1
            logging.warn(
                'Skip {} with too many preds ({} / {} are reachable)'.format(
                    name, len(reachable_pred), pkg.in_degree()))
            continue
        else:
            logging.info('Processing {} with {} preds'.format(
                name, pkg.in_degree()))

        # if the package does not have popcon data, then skip
        target_daily_info = get_daily_info(name)
        if target_daily_info is None:
            continue
        edges = pkg.in_edges()
        candidate_nodes = [vp[x.source()]['label'] for x in edges]
        candidate_nodes.append(name)
        nodes = []
        daily_info_list = []
        for pkg_name in candidate_nodes:
            daily_info = get_daily_info(pkg_name)
            if daily_info is None:
                continue
            nodes.append(pkg_name)
            daily_info_list.append(daily_info)
        factor_table = []
        for i in range(0, int(math.pow(2, len(nodes)))):
            bin_vector = list('{}'.format(get_bin(i, len(nodes))))
            cond_prob = compute_conditional_probability(
                nodes, daily_info_list, bin_vector)
            factor_table.append(cond_prob)
        factors.append((nodes, factor_table))

    with open('{}.fg'.format(args.package), 'w') as f:
        f.write('{}\n\n'.format(len(factors)))
        for (nodes, factor_table) in factors:
            print_factor(name2idx, nodes, factor_table, f)
    result['size'] = count
    return result


class VisitorExample(graph_tool.search.DFSVisitor):
    def __init__(self, nodes):
        self.nodes = nodes

    def discover_vertex(self, u):
        self.nodes.add(u)


def compute_reachable_nodes(args, g, name2idx):
    reachable_nodes = set()
    graph_tool.search.dfs_search(g, name2idx[args.package],
                                 VisitorExample(reachable_nodes))
    logging.info("Found {} reachable nodes".format(len(reachable_nodes)))
    return reachable_nodes


parser = ArgumentParser()
parser.add_argument("-d", "--debug", dest='debug', action='store_true')
parser.add_argument("-m", "--max-pred", dest='max_pred', type=int, default=15)
parser.add_argument("package")


def main():
    args = parser.parse_args()
    print('Building Bayesian network for {}...'.format(args.package))
    start = time.process_time()
    with open(DEPS_PATH) as f:
        deps = json.load(f)
    g, name2idx = build(deps)
    reachable_nodes = compute_reachable_nodes(args, g, name2idx)
    result = generate_factor_graph(args, g, name2idx, reachable_nodes)
    logging.info('Skipped nodes: {}'.format(result['skipped']))
    print('\nDone ({}sec)'.format(int(time.process_time() - start)))


if __name__ == '__main__':
    main()
