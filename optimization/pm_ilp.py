#!/usr/bin/env python3

import math
import csv
import sys

NAME = 0
CVE = 1
GADGET = 2
INSTALL_SIZE = 3

def create_string(alpha, all_packages, test_cases, cve_flag=1, num_flag=0, gadget_flag=0, install_size_flag=0):
  # minimize
  minimization_str = "Minimize\n"
  
  # minimize the number of CVEs
  if (cve_flag):
    for i in range(len(all_packages)):
      minimization_str += str(int(all_packages[i][CVE])) + " " + "x" + str(i) + " + "
    minimization_str = minimization_str[:-2] + "\n"
  
  # minimize the number of installed packages
  if (num_flag):
    for i in range(len(all_packages)):
      minimization_str += "x" + str(i) + " + "
    minimization_str = minimization_str[:-2] + "\n"

  # minimize the number of gadgets
  if (gadget_flag):
    for i in range(len(all_packages)):
      minimization_str += str(int(all_packages[i][GADGET])) + " " + "x" + str(i) + " + "
    minimization_str = minimization_str[:-2] + "\n"

  # minimize the total installed size
  if (install_size_flag):
    #minimization_str += "obj: Priority=1 Weight=1 AbsTol=0 RelTol=0\n"
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


def get_data(all_packages_file, test_cases_file, votes_file):
  print(votes_file)
  all_packages = []
  test_cases = []
  repeats = []
  package_mapping = dict()
  with open(all_packages_file) as f:
    csv_reader = csv.reader(f, delimiter=' ')
    index = 0
    for row in csv_reader:
      # name, cve, gadgets, installed_size
      all_packages.append((row[NAME], row[CVE], row[GADGET], row[INSTALL_SIZE]))
      package_mapping[row[NAME]] = index
      index += 1
  
  #with open(votes_file) as f:
   # csv_reader = csv.reader(f, delimiter=' ')
    #repeats = []
    #for row in csv_reader:
     # repeats.append(int(row[0]) + 1)

  with open(test_cases_file) as f:
    csv_reader = csv.reader(f, delimiter=' ')
    index = 0
    for row in csv_reader:
      test_case = []
      test_case.append(package_mapping.get(package_name))
      for i in range(0, len(row)):
        row[i] = row[i].strip()
        if row[i] != "":
          if row[i] == 'nodep':
            continue
          else:
            test_case.append(package_mapping.get(row[i]))
      for i in range(1):#(repeats[index]):
        test_cases.append(test_case)
      index += 1

  return all_packages, test_cases


if __name__ == '__main__':
  # get command-line arguments
  alpha = float(sys.argv[1])
  all_packages_file = sys.argv[2]
  test_cases_file = sys.argv[3]
  votes_file = sys.argv[4]
  package_name = sys.argv[5]
  lp_file = sys.argv[6]


  # get data
  all_packages, test_cases = get_data(all_packages_file, test_cases_file, votes_file)
  
  # create ilp string 
  ilp_formulation = create_string(alpha, all_packages, test_cases)
  # write ilp string to file
  with open(lp_file, 'w') as f:
    print(f"{ilp_formulation}", file=f)
