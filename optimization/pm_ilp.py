#!/usr/bin/env python3

import math
import csv
import sys

def create_string(alpha, all_packages, test_cases):
  # minimize
  minimization_str = "Minimize\n"
  for i in range(len(all_packages)):
    minimization_str += str(all_packages[i][1]) + " " + "x" + str(i) + " + "
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
    c1_str = c1_str + " > " + "-"  + str(ones) + "\n"
  
  # constraint type (2)
  c2_str = "c2: "
  for i in range(len(test_cases)):
    c2_str += "x" + str(i) + " - " + str(len(test_cases[i])) + " y" + str(i) + " + "
  c2_str = c2_str[:-2] + ">= 0" + "\n"
  
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
  with open(all_packages_file) as f:
    csv_reader = csv.reader(f, delimiter=',')
    for row in csv_reader:
      all_packages.append((row[0], row[1]))

  with open(test_cases_file) as f:
    csv_reader = csv.reader(f, delimiter=',')
    for row in csv_reader:
      test_case = []
      for i in row:
        test_case.append(i)
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
