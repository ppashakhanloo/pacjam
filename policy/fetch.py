#!/usr/bin/python3

import json
import os
import requests

REPO_HOME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEPS_PATH = os.path.join(REPO_HOME, 'deps.json')
POPCON_PATH = os.path.join(REPO_HOME, 'popcon-data')
BLACKLIST_PATH = '{}/policy/blacklist.json'.format(REPO_HOME)
url_prefix = 'https://qa.debian.org/cgi-bin/popcon-data?'

with open(BLACKLIST_PATH, 'r') as f:
    black_list = json.load(f)


def load_data(pkg):
    json_file = '{}/{}.json'.format(POPCON_PATH, pkg)
    if pkg in black_list or pkg[0] == '<':
        return {}
    if os.path.exists(json_file):
        with open(json_file) as f:
            data = json.load(f)
    else:
        url = url_prefix + 'packages={}'.format(pkg)
        try:
            r = requests.get(url)
        except:
            print('WARN: cannot get {}'.format(url))
            black_list.append(pkg)
            with open(BLACKLIST_PATH, 'w') as f:
                json.dump(black_list, f, indent=2)
            return {}
        data = json.loads(r.content)
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    return data


def main():
    with open(DEPS_PATH) as f:
        deps = json.load(f)
    count = 1
    for pkg in deps:
        print('[{}/{}] Processing {}...'.format(count, len(deps), pkg))
        load_data(pkg)
        count += 1


if __name__ == '__main__':
    main()
