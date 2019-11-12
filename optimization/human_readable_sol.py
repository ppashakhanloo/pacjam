#!/usr/bin/env python3

import math
import csv
import sys

NAME = 0
CVE = 1
GADGET = 2
INSTALL_SIZE = 3

def get_data(sol_file, tdeps_file):
  packages = dict()
  traces = []
  with open(tdeps_file) as f:
    csv_reader = csv.reader(f, delimiter=' ')
    index = 0
    for row in csv_reader:
      packages[index] = row[NAME]
      index += 1
  
  with open(sol_file) as f:
    csv_reader = csv.reader(f, delimiter=' ')
    index = 0
    trace = []
    for row in csv_reader:
      if not row[0].startswith('x'):
        continue
      if not row[1].startswith('1'):
        continue
      trace.append(packages.get(int(row[0][1:])))

  return trace

if __name__ == '__main__':
  # get command-line arguments
  sol_file = sys.argv[1]
  tdeps_file = sys.argv[2]
  
  trace = get_data(sol_file, tdeps_file)
  print(trace)
