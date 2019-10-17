#!/usr/bin/python3

import json
import os
import sys

from datetime import date
from dateutil.rrule import rrule, DAILY

REPO_HOME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEPS_PATH = os.path.join(REPO_HOME, 'deps.json')
POPCON_PATH = os.path.join(REPO_HOME, 'popcon-data')

start_date = date(2004, 1, 1)
end_date = date(2019, 10, 4)


def load_data(pkg):
    try:
        with open('{}/{}.json'.format(POPCON_PATH, pkg)) as f:
            data = json.load(f)
        return data
    except:
        print(pkg)
        sys.exit(1)


def process_pkg(pkg):
    if not os.path.exists('{}/{}.json'.format(POPCON_PATH, pkg)):
        return None
    if os.path.exists('{}/{}.daily.json'.format(POPCON_PATH, pkg)):
        return None
    data = load_data(pkg)
    if pkg not in data:
        return None
    daily_use_data = {}
    daily_use_data[pkg] = {}
    vote_prev = 0
    for dt in rrule(DAILY, dtstart=start_date, until=end_date):
        date = dt.strftime("%Y-%m-%d")
        if date not in data[pkg]:
            continue
        vote = data[pkg][date]['vote']
        daily_use_data[pkg][date] = {}
        daily_use_data[pkg][date]['vote'] = vote
        if vote > vote_prev:
            daily_use_data[pkg][date]['binary'] = True
        else:
            daily_use_data[pkg][date]['binary'] = False
        vote_prev = vote
    return daily_use_data


def main():
    with open(DEPS_PATH) as f:
        deps = json.load(f)
    count = 1
    for pkg in deps:
        print('[{}/{}] Processing {}...'.format(count, len(deps), pkg))
        daily_use_data = process_pkg(pkg)
        if daily_use_data is not None:
            with open('{}/{}.daily.json'.format(POPCON_PATH, pkg), 'w') as f:
                json.dump(daily_use_data, f, indent=2)
        count += 1


if __name__ == '__main__':
    main()
