#!/usr/bin/env python3

import math
import csv
import sys

NAME = 0
CVE = 1
GADGET = 2
INSTALL_SIZE = 3

def create_string(alpha, all_packages, test_cases, cve_flag=1, num_flag=1, gadget_flag=0, install_size_flag=0):
  # minimize
  minimization_str = "Minimize multi-objectives\n"
  
  # minimize the number of CVEs
  if (cve_flag):
    minimization_str += "obj1: Priority=1 Weight=1 AbsTol=0 RelTol=0\n"
    for i in range(len(all_packages)):
      minimization_str += str(int(all_packages[i][CVE])) + " " + "x" + str(i) + " + "
    minimization_str = minimization_str[:-2] + "\n"
  
  # minimize the number of installed packages
  if (num_flag):
    minimization_str += "obj2: Priority=2 Weight=1 AbsTol=0 RelTol=0\n"
    for i in range(len(all_packages)):
      minimization_str += "x" + str(i) + " + "
  minimization_str = minimization_str[:-2] + "\n"

  # minimize the number of gadgets
  if (gadget_flag):
    minimization_str += "obj3: Priority=3 Weight=1 AbsTol=0 RelTol=0\n"
    for i in range(len(all_packages)):
      minimization_str += str(int(all_packages[i][GADGET])) + " " + "x" + str(i) + " + "
    minimization_str = minimization_str[:-2] + "\n"

  # minimize the total installed size
  if (install_size_flag):
    minimization_str += "obj4: Priority=4 Weight=1 AbsTol=0 RelTol=0\n"
    for i in range(len(all_packages)):
      minimization_str += str(int(all_packages[i][INSTALL_SIZE])) + " " + "x" + str(i) + " + "
    minimization_str = minimization_str[:-2] + "\n"

  subject_to_str = "Subject To\n"
  # constraint type (1)
  c1_str = ""
  for i in range(len(test_cases)):
    ones = 0
    c1_str += "c1" + str(i) + ": "
    c1_str += "y" + str(i)
    for j in range(len(test_cases[i])):
      ones += 1
      c1_str += " - x" + str(test_cases[i][j])
    c1_str += " > " + "-"  + str(ones) + "\n"
  
  # constraint type (2)
  c2_str = ""
  for i in range(len(test_cases)):
    c2_str += "c2" + str(i) + ": "
    for j in range(len(test_cases[i])):
      c2_str += "x" + str(test_cases[i][j]) + " + "
    c2_str = c2_str[:-2]
    c2_str += " - " + str(len(test_cases[i])) + " " + "y" + str(i)
    c2_str += " >= 0" + "\n"
  
  # constraint type (3)
  c3_str = "c3: "
  for i in range(len(test_cases)):
    c3_str += "y" + str(i) + " + "
  thresh = int(math.floor(alpha * len(test_cases)))
  c3_str = c3_str[:-2] + ">= " + str(thresh) + "\n"
  
  # variables
  variable_definitions = "Binary\n"
  var_str = ""
  for i in range(len(all_packages)):
    var_str += " x" + str(i)
  for i in range(len(test_cases)):
    var_str += " y" + str(i)
  var_str = var_str[1:] + "\n"

  # end
  end_str = "End"

  return minimization_str \
         + subject_to_str + c1_str + c2_str + c3_str \
         + variable_definitions + var_str \
         + end_str


def get_data(all_packages_file, test_cases_file):
  all_packages = []
  test_cases = []
  package_mapping = dict()
  with open(all_packages_file) as f:
    csv_reader = csv.reader(f, delimiter=' ')
    for row in csv_reader:
      # index, name, cve
      all_packages.append((row[1], row[2]))
      package_mapping[row[1]] = int(row[0])

  with open(test_cases_file) as f:
    csv_reader = csv.reader(f, delimiter=' ')
    for row in csv_reader:
      test_case = []
      for i in row:
        i = i.strip()
        if i != "":
          test_case.append(package_mapping.get(i))
      test_cases.append(test_case)
  return all_packages, test_cases


if __name__ == '__main__':
  # get command-line arguments
  alpha = float(sys.argv[1])
  all_packages_file = sys.argv[2]
  test_cases_file = sys.argv[3]
  lp_file = sys.argv[4]

  # get data
  all_packages, test_cases = get_data(all_packages_file, test_cases_file)
  
  # create ilp string 
  ilp_formulation = create_string(alpha, all_packages, test_cases)
  # write ilp string to file
  with open(lp_file, 'w') as f:
    print(f"{ilp_formulation}", file=f)
