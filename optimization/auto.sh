#!/bin/bash

alphas=(
"0.1"
"0.2"
"0.3"
"0.4"
"0.5"
"0.6"
"0.7"
"0.8"
"0.9"
"1.0"
)

package=$1

for a in ${alphas[@]}; do
  python3 pm_ilp.py $a $package.tdeps $package.traces $package.votes $package $package-$a.lp
  gurobi_cl ResultFile=$package-$a.sol $package-$a.lp
done
