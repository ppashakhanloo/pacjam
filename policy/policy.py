#!/usr/bin/python3

import json
import os
import requests
import sys
import logging
import time

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


def compute_naive_policy(args, target_daily_info, dep_daily_info):
    num_installed = 0
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


# TODO
def static_policy(args, deps):
    return None


# TODO
def dynamic_policy(args, deps):
    return None


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
