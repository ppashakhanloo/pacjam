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


number_of_new_id = 0


def get_new_id(g):
    global number_of_new_id
    newid = g.num_vertices() + number_of_new_id
    number_of_new_id += 1
    return newid


def store_vertex_dict(g):
    with open('{}/{}/bnet-dict.txt'.format(REPO_HOME, 'policy'), 'w') as f:
        for pkg in g.vertices():
            f.write(
                '{}: {}\n'.format(g.vertex_index[pkg],
                                  g.vertex_properties['info'][pkg]['label']))
        # for unreachable nodes
        for i in range(0, number_of_new_id):
            n = g.num_vertices() + i
            f.write('{}: dummy{}\n'.format(n, n))


def get_bin(x, n):
    return format(x, 'b').zfill(n)


def get_daily_info(pkg):
    filename = '{}/{}.daily.json'.format(POPCON_PATH, pkg)
    if not os.path.exists(filename):
        return None
    with open(filename) as f:
        data = json.load(f)
    return data


def match(daily_info, date, bit):
    if date not in daily_info:
        answer = False
    else:
        answer = daily_info[date]['binary']
    return bool(int(bit)) == answer


def match_exists(unreachable_daily_info_list, date):
    for pred, daily_info in unreachable_daily_info_list:
        if date not in daily_info[pred]:
            answer = False
        else:
            answer = daily_info[pred][date]['binary']
        if answer:
            return True
    return False


def match_all(unreachable_daily_info_list, date):
    for pred, daily_info in unreachable_daily_info_list:
        if date not in daily_info[pred]:
            answer = False
        else:
            answer = daily_info[pred][date]['binary']
        if answer:
            return False
    return True


def compute_conditional_probability(target, target_daily_info,
                                    reachable_daily_info_list,
                                    unreachable_daily_info_list, bin_vector):
    assert len(reachable_daily_info_list) + 2 == len(bin_vector)
    hypothesis_date = 0
    conclusion_date = 0
    for date in target_daily_info[target]:
        # count the number of days where the hypothesis matches
        hypothesis_hit = True
        i = 0
        for pred, reachable_daily_info in reachable_daily_info_list:
            hypothesis_hit = hypothesis_hit and match(
                reachable_daily_info[pred], date, bin_vector[i])
            i += 1
        if hypothesis_hit:
            # if there is no unreachable pred, hit
            if len(unreachable_daily_info_list) == 0:
                hypothesis_date += 1
            # if there exists at least one use of unreachable node then it is used
            elif bool(int(bin_vector[-2])) and match_exists(
                    unreachable_daily_info_list, date):
                hypothesis_date += 1
            # if all unreachable nodes do not use then hit then it is not used
            elif not bool(int(bin_vector[-2])) and match_all(
                    unreachable_daily_info_list, date):
                hypothesis_date += 1
            else:
                hypothesis_hit = False

        # count the number of days where the conclusion matches
        conclusion_hit = match(target_daily_info[target], date, bin_vector[-1])
        if hypothesis_hit and conclusion_hit:
            conclusion_date += 1
    if hypothesis_date == 0:
        return 0
    else:
        return float(conclusion_date) / float(hypothesis_date)


# https://staff.fnwi.uva.nl/j.m.mooij/libDAI/doc/fileformats.html
def print_factor(g, name2idx, info, factor_table, f):
    # number of nodes
    f.write(str(len(info['reachable']) + 2) + "\n")
    # node ids
    s = ""
    for node, _ in info['reachable']:
        s = s + str(name2idx[node]) + " "
    if len(info['unreachable']) > 0:
        s = s + str(get_new_id(g)) + " "
    s = s + str(name2idx[info['package']])
    f.write(s + "\n")
    # arity
    s = ""
    for i in range(0, len(info['reachable']) + 2):
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

        # if the package does not have popcon data, then skip
        target_daily_info = get_daily_info(name)
        if target_daily_info is None:
            continue

        reachable_preds = [
            vp[p.source()]['label'] for p in pkg.in_edges()
            if p.source() in reachable_nodes
        ]
        unreachable_preds = [
            vp[p.source()]['label'] for p in pkg.in_edges()
            if p.source() not in reachable_nodes
        ]
        if len(reachable_preds) > args.max_pred:
            result['skipped'] += 1
            logging.warn(
                'Skip {} with too many preds ({} / {} are reachable)'.format(
                    name, len(reachable_preds), pkg.in_degree()))
            continue
        else:
            logging.info('Processing {} with {} / {} reachable preds'.format(
                name, len(reachable_preds), pkg.in_degree()))
        # if the package does not have popcon data, then skip
        reachable_daily_info_list = []
        for pred in reachable_preds:
            daily_info = get_daily_info(pred)
            if daily_info is not None:
                reachable_daily_info_list.append((pred, daily_info))

        unreachable_daily_info_list = []
        for pred in unreachable_preds:
            daily_info = get_daily_info(pred)
            if daily_info is not None:
                unreachable_daily_info_list.append((pred, daily_info))

        factor_table = []
        # consider len(reachable) + 2 variables. one is for the target, the other is an aggregation of all unreachable
        bitvector_length = len(reachable_daily_info_list) + 2
        for i in range(0, int(math.pow(2, bitvector_length))):
            bin_vector = list('{}'.format(get_bin(i, bitvector_length)))
            cond_prob = compute_conditional_probability(
                name, target_daily_info, reachable_daily_info_list,
                unreachable_daily_info_list, bin_vector)
            factor_table.append(cond_prob)
        info = {
            'reachable': reachable_daily_info_list,
            'unreachable': unreachable_daily_info_list,
            'package': name
        }
        factors.append((info, factor_table))

    with open('{}.fg'.format(args.package), 'w') as f:
        f.write('{}\n\n'.format(len(factors)))
        for (info, factor_table) in factors:
            print_factor(g, name2idx, info, factor_table, f)
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
    store_vertex_dict(g)
    logging.info('Skipped nodes: {}'.format(result['skipped']))
    print('\nDone ({}sec)'.format(int(time.process_time() - start)))


if __name__ == '__main__':
    main()
