#!/usr/bin/python3

import json
import os
import requests
import multiprocessing

REPO_HOME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEPS_PATH = os.path.join(REPO_HOME, 'deps.json')
POPCON_PATH = os.path.join(REPO_HOME, 'popcon-data')
BLACKLIST_PATH = '{}/policy/blacklist.json'.format(REPO_HOME)
url_prefix = 'https://qa.debian.org/cgi-bin/popcon-data?'

count = 0
total = 0


def load_blacklist():
    with open(BLACKLIST_PATH, 'r') as f:
        blacklist = json.load(f)
    return blacklist


# TODO: lock may be heavy-weight
def add_blacklist(pkg):
    lock.acquire()
    blacklist = load_blacklist()
    blacklist.append(pkg)
    with open(BLACKLIST_PATH, 'w') as f:
        json.dump(blacklist, f, indent=2)
    lock.release()


def load_data(pkg):
    global total
    total_work = int(total / multiprocessing.cpu_count())
    lock.acquire()
    global count
    print('[{}/{}] Processing {}...'.format(count, total_work, pkg))
    count += 1
    blacklist = load_blacklist()
    lock.release()
    json_file = '{}/{}.json'.format(POPCON_PATH, pkg)
    if pkg in blacklist or pkg[0] == '<':
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
            add_blacklist(pkg)
            return {}
        data = json.loads(r.content)
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    return data


def init(l):
    global lock
    lock = l


def main():
    global total
    with open(DEPS_PATH) as f:
        deps = json.load(f)
    total = len(deps)
    lock = multiprocessing.Lock()
    pool = multiprocessing.Pool(initializer=init, initargs=(lock, ))
    pool.map(load_data, [pkg for pkg in deps])
    pool.close()


#    for pkg in deps:
#        print('[{}/{}] Processing {}...'.format(count, len(deps), pkg))
#        load_data(pkg)
#        count += 1

if __name__ == '__main__':
    main()
