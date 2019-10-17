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


blacklist = {'libc6'}


def build(deps):
    g = graph_tool.Graph()
    name2idx = {}
    v_prop = g.new_vertex_property('object')

    counter = 0

    for name, depends in deps.items():
        if name in blacklist:
            continue
        counter += 1
        src = get_vertex(g, name2idx, v_prop, name)
        edges = []
        for dep_name in depends:
            if dep_name in blacklist:
                continue
            dst = get_vertex(g, name2idx, v_prop, dep_name)
            edges.append((src, dst))
        g.add_edge_list(edges)

    g.vertex_properties['info'] = v_prop
    return g, name2idx


number_of_new_id = 0
id_dict = {}


def get_new_id():
    global number_of_new_id
    newid = number_of_new_id
    number_of_new_id += 1
    return newid


def store_id_dict(name, nid):
    global id_dict
    id_dict[name] = nid


def store_result(args, g, reachable, name2idx, result):
    factors = result['factors']
    with open('{}/{}/{}.dict'.format(REPO_HOME, 'policy', args.package),
              'w') as f:
        global id_dict
        for name, nid in id_dict.items():
            f.write('{}: {}\n'.format(nid, name))

    with open('{}.fg'.format(args.package), 'w') as f:
        f.write('{}\n\n'.format(len(factors)))
        for pkg, factor in factors.items():
            print_factor(g, factor, f)

    with open('{}/{}/{}.reachable.json'.format(REPO_HOME, 'policy',
                                               args.package), 'w') as f:
        vp = g.vertex_properties['info']
        l = [vp[x]['label'] for x in reachable]
        json.dump(l, f, indent=2)


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
    for pred, daily_info in unreachable_daily_info_list.items():
        if date not in daily_info[pred]:
            answer = False
        else:
            answer = daily_info[pred][date]['binary']
        if answer:
            return True
    return False


def match_all(unreachable_daily_info_list, date):
    for pred, daily_info in unreachable_daily_info_list.items():
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
    # compute probability of even number of binary vector
    # Note:
    # - 0th element of bin_vector is conclusion
    # - 1st element of bin_vector is unreachable (if unreachable exists)
    # - the other elements are hyphotheses (n, n-1, ..., 0th element of reachable) (if exists)
    hypothesis_date = 0
    conclusion_date = 0

    for date in target_daily_info[target]:
        # count the number of days where the hypothesis matches
        hypothesis_hit = True
        i = 0
        for pred, reachable_daily_info in reachable_daily_info_list.items():
            hypothesis_hit = hypothesis_hit and match(
                reachable_daily_info[pred], date, bin_vector[-i - 1])
            i += 1

        if hypothesis_hit:
            # if there is no unreachable pred, hit
            if len(unreachable_daily_info_list) == 0:
                hypothesis_date += 1
            # if there exists at least one use of unreachable node then it is used
            elif bool(int(bin_vector[1])) and match_exists(
                    unreachable_daily_info_list, date):
                hypothesis_date += 1
            # if all unreachable nodes do not use then hit then it is not used
            elif not bool(int(bin_vector[1])) and match_all(
                    unreachable_daily_info_list, date):
                hypothesis_date += 1
            else:
                hypothesis_hit = False

        # count the number of days where the conclusion matches
        conclusion_hit = match(target_daily_info[target], date, bin_vector[0])
        if hypothesis_hit and conclusion_hit:
            conclusion_date += 1
    # if there is no maching data, assign 0.5
    if hypothesis_date == 0:
        return 0.5
    else:
        return float(conclusion_date) / float(hypothesis_date)


# https://staff.fnwi.uva.nl/j.m.mooij/libDAI/doc/fileformats.html
def print_factor(g, factor, f):
    global id_dict
    # number of nodes
    length = len(factor['reachable']) + int(factor['unreachable'] != []) + 1
    f.write(str(length) + "\n")
    # node ids
    s = ""
    for node in factor['reachable']:
        s = str(id_dict[node]) + " " + s
    if factor['unreachable_id'] is not None:
        s = str(factor['unreachable_id']) + " " + s
    s = str(factor['id']) + " " + s
    f.write(s + "\n")
    # arity
    s = ""
    for i in range(0, length):
        s = s + "2 "
    f.write(s + "\n")
    count = 0
    factor_table = factor['factor_table']
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


def partition_preds(vp, pkg, reachable_nodes):
    reachable_preds = [
        vp[p.source()]['label'] for p in pkg.in_edges()
        if p.source() in reachable_nodes
    ]
    unreachable_preds = [
        vp[p.source()]['label'] for p in pkg.in_edges()
        if p.source() not in reachable_nodes
    ]
    return reachable_preds, unreachable_preds


def daily_information(preds):
    daily_info_list = {}
    for pred in preds:
        daily_info = get_daily_info(pred)
        # if the package does not have popcon data, then skip
        if daily_info is not None:
            daily_info_list[pred] = daily_info
    return daily_info_list


def generate_factor_table(name, target_daily_info, reachable_daily_info_list,
                          unreachable_daily_info_list):
    factor_table = []

    if len(reachable_daily_info_list) + len(unreachable_daily_info_list) == 0:
        # if it is dummy node, only 1 bit
        bitvector_length = 1
    else:
        # if not dummy node, consider len(reachable) + 2 variables.
        # one is for the target, the other is an aggregation of all unreachable
        bitvector_length = len(reachable_daily_info_list) + int(
            unreachable_daily_info_list != []) + 1
    for i in range(0, int(math.pow(2, bitvector_length)), 2):
        bin_vector = list(reversed('{}'.format(get_bin(i, bitvector_length))))
        cond_prob = compute_conditional_probability(
            name, target_daily_info, reachable_daily_info_list,
            unreachable_daily_info_list, bin_vector)
        factor_table.append(cond_prob)
        factor_table.append(1.0 - cond_prob)
    return factor_table


def merge_daily_info(name, daily_info_list):
    all_keys = set()
    for pkg, info in daily_info_list.items():
        all_keys.update(set(info[pkg].keys()))
    merged = {}
    for date in all_keys:
        binary = False
        vote = 0
        for pkg, info in daily_info_list.items():
            # if there exists at least one use, then it is used
            if date in info[pkg]:
                binary = binary or info[pkg][date]['binary']
                vote = vote + info[pkg][date]['vote']
        merged[date] = {'vote': vote, 'binary': binary}
    info[name] = merged
    return info


def generate_factor_graph(args, g, reachable_nodes):
    vp = g.vertex_properties['info']
    total = len(reachable_nodes)
    count = 0
    result = {}
    result['pruned'] = 0
    factors = {}
    for pkg in reachable_nodes:
        count += 1
        name = vp[pkg]['label']
        print('[{}/{}] Processing nodes...'.format(count, total), end='\r')

        # if the package does not have popcon data, then skip
        target_daily_info = get_daily_info(name)
        if target_daily_info is None:
            continue

        reachable_preds, unreachable_preds = partition_preds(
            vp, pkg, reachable_nodes)

        if len(reachable_preds) > args.max_pred:
            result['pruned'] += 1
            logging.warn(
                'Prune preds of {} with too many preds ({} / {} are reachable)'.
                format(name, len(reachable_preds), pkg.in_degree()))
            reachable_preds = reachable_preds[0:args.max_pred]
        else:
            logging.info('Processing {} with {} / {} reachable preds'.format(
                name, len(reachable_preds), pkg.in_degree()))
        reachable_daily_info_list = daily_information(reachable_preds)
        unreachable_daily_info_list = daily_information(unreachable_preds)

        factor_table = generate_factor_table(name, target_daily_info,
                                             reachable_daily_info_list,
                                             unreachable_daily_info_list)

        if len(unreachable_preds) > 0:
            uid = get_new_id()
            uname = 'dummy{}'.format(uid)
            store_id_dict(uname, uid)
            merged_daily_info = merge_daily_info(uname,
                                                 unreachable_daily_info_list)
            factors[uname] = {
                'reachable': [],
                'unreachable': [],
                'factor_table':
                generate_factor_table(uname, merged_daily_info, {}, {}),
                'id':
                uid,
                'unreachable_id':
                None,
                'name':
                uname
            }
        else:
            uid = None

        nid = get_new_id()
        store_id_dict(name, nid)
        info = {
            'reachable': reachable_daily_info_list,
            'unreachable': unreachable_daily_info_list,
            'factor_table': factor_table,
            'id': nid,
            'unreachable_id': uid,
            'name': name
        }
        factors[name] = info

    result['size'] = count
    result['factors'] = factors
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
    result = generate_factor_graph(args, g, reachable_nodes)
    store_result(args, g, reachable_nodes, name2idx, result)
    logging.info('# nodes with pruned preds: {}'.format(result['pruned']))
    print('\nDone ({} sec)'.format(int(time.process_time() - start)))


if __name__ == '__main__':
    main()
