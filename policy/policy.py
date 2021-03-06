#!/usr/bin/python3

import json
import os
import requests
import sys
import logging
import time
import subprocess

from datetime import date
from dateutil.rrule import rrule, DAILY
from argparse import ArgumentParser

REPO_HOME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEPS_PATH = os.path.join(REPO_HOME, 'deps.json')
POPCON_PATH = os.path.join(REPO_HOME, 'popcon-data')

logging.basicConfig(
    filename='policy.log',
    filemode='w',
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")

start_date = date(2004, 1, 1)
end_date = date(2019, 10, 4)


def save_statistics(args, result):
    with open('{}.{}.json'.format(args.package, args.command), 'w') as f:
        json.dump(result, f, indent=2)


def get_daily_info(pkg):
    filename = '{}/{}.daily.json'.format(POPCON_PATH, pkg)
    if not os.path.exists(filename):
        return None
    with open(filename) as f:
        data = json.load(f)
    return data


def compute_static_policy(args, dep_daily_info):
    num_installed = 0
    num_used = 0
    for dt in rrule(DAILY, dtstart=start_date, until=end_date):
        dtstr = dt.strftime("%Y-%m-%d")
        if dtstr in dep_daily_info:
            num_installed += 1
            if dep_daily_info[dtstr]['binary']:
                num_used += 1
    distrib = {}
    distrib['installed'] = num_installed
    distrib['used'] = num_used
    distrib['prob'] = float(num_used) / float(num_installed)
    return distrib


def compute_naive_policy(args, target_daily_info, dep_daily_info):
    num_commonly_installed = 0
    num_used = 0
    num_commonly_used = 0
    for dt in rrule(DAILY, dtstart=start_date, until=end_date):
        dtstr = dt.strftime("%Y-%m-%d")
        if dtstr in target_daily_info and dtstr in dep_daily_info:
            num_commonly_installed += 1
            if target_daily_info[dtstr]['binary']:
                num_used += 1
            if target_daily_info[dtstr]['binary'] and dep_daily_info[dtstr]['binary']:
                num_commonly_used += 1
    joint = {}
    joint['commonly_installed'] = num_commonly_installed
    joint['used'] = num_used
    joint['commonly_used'] = num_commonly_used
    joint['prob'] = float(num_commonly_used) / float(num_used)
    return joint


def static_policy(args, deps):
    dependent_packages = deps[args.package]
    logging.info('Dependent packages:')
    logging.info(dependent_packages)

    target_daily_info = get_daily_info(args.package)
    result = {}
    info = compute_static_policy(args, target_daily_info[args.package])
    result[args.package] = info
    for dep in dependent_packages:
        dep_daily_info = get_daily_info(dep)
        info = compute_static_policy(args, dep_daily_info[dep])
        result[dep] = info
    return result


def read_dictionary(dict_file):
    dictionary = {}
    for line in open(dict_file):
        line = line.strip()
        if len(line) == 0: continue
        components = [
            c.strip() for c in line.split(': ') if len(c.strip()) > 0
        ]
        assert len(components) == 2
        dictionary[components[1]] = components[0]
    return dictionary


def exec_wrapper_cmd(ps, cmd):
    logging.info('Driver to wrapper: ' + cmd)
    print(cmd, file=ps.stdin)
    ps.stdin.flush()
    response = ps.stdout.readline().strip()
    logging.info('Wrapper to driver: ' + response)
    return response


def dynamic_policy(args, deps):
    with open(args.installed) as f:
        installed_packages = json.load(f)
    bnet_dict = read_dictionary(args.dict)
    candidate = set()
    for installed in installed_packages:
        candidate.update(deps[installed])
    with open('solver.log', 'w') as f:
        with subprocess.Popen(
            [args.solver, args.fg],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=f,
                universal_newlines=True) as ps:
            # mark all installed packages as true
            for pkg in installed_packages:
                cmd = 'O {} true'.format(bnet_dict[pkg])
                exec_wrapper_cmd(ps, cmd)
            # perform belief propagation
            exec_wrapper_cmd(ps, 'BP 1e-06 500 1000 100')
            prob = {}
            for pkg in candidate:
                if pkg not in bnet_dict:
                    logging.warn('{} not found'.format(pkg))
                    continue
                prob[pkg] = {}
                prob[pkg]['prob'] = exec_wrapper_cmd(ps, 'Q {}'.format(
                    bnet_dict[pkg]))
    return prob


def naive_policy(args, deps):
    dependent_packages = deps[args.package]
    logging.info('Dependent packages:')
    logging.info(dependent_packages)

    target_daily_info = get_daily_info(args.package)
    result = {}
    info = compute_naive_policy(args, target_daily_info[args.package],
                                target_daily_info[args.package])
    result[args.package] = info
    for dep in dependent_packages:
        dep_daily_info = get_daily_info(dep)
        info = compute_naive_policy(args, target_daily_info[args.package],
                                    dep_daily_info[dep])
        result[dep] = info
    return result


parser = ArgumentParser()
subparsers = parser.add_subparsers(dest='command')
parser_static = subparsers.add_parser('static')
parser_static.add_argument("package")
parser_dynamic = subparsers.add_parser('dynamic')
parser_dynamic.add_argument("package")
parser_dynamic.add_argument("--installed", dest='installed')
parser_dynamic.add_argument("--fg", dest='fg')
parser_dynamic.add_argument("--dict", dest='dict')
parser_dynamic.add_argument("--solver", dest='solver')
parser_naive = subparsers.add_parser('naive')
parser_naive.add_argument("package")


def main():
    args = parser.parse_args()
    print('Installation policy for {}...'.format(args.package))
    start = time.process_time()
    with open(DEPS_PATH) as f:
        deps = json.load(f)
    if args.command == 'static':
        result = static_policy(args, deps)
    elif args.command == 'dynamic':
        result = dynamic_policy(args, deps)
    elif args.command == 'naive':
        result = naive_policy(args, deps)
    else:
        print('Invalid')
    save_statistics(args, result)
    print('Done ({} sec)'.format(int(time.process_time() - start)))


if __name__ == '__main__':
    main()
