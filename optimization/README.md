## Requirements
- Gurobi solver (the academic license is free)
- Python3

## Quick Start
`$ ./auto.sh <package_nam>`
For alpha=0.1 ... 1.0,
this script will first generate .lp files from traces.
Next, it will solve every .lp file.
Finally, it will transform .sol results to a human-readable format.

## Usage
`$ python3 pm_ilp.py <alpha> <package_file> <test_cases_file> <output_file>`

### `alpha`
A number between 0 and 1

### `package_file`
A comma-separated CSV file in which the first column is the package name, and
the second column is the number of CVEs.

### `test_cases_file`
A CSV file in which the every row is a comma-separated list of
the packages that are used in each test-case.

### `output_file`
A `.lp` file that contains the LP formulation that will be fed to Gurobi.
