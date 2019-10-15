import sys

inst, vote = input().split()
use_ratio = -1 

if float(inst) > 0:
  use_ratio = float(vote) / float(inst)

width=1

if use_ratio == 0:
  width=2
if use_ratio > 0 and use_ratio < 0.25:
  width=3
if use_ratio >= 0.25 and use_ratio < 0.5:
  width=4
if use_ratio >= 0.5 and use_ratio < 0.75:
  width=5
if use_ratio >= 0.75:
  width=6

print(width)
