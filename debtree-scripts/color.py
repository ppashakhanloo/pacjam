import sys

this_cves, all_cves = input().split()

power = 0.0
if float(all_cves) > 0:
  power = float(this_cves) / float(all_cves)
else:
  power = 0.0

red = 0.0
green = 0.0
blue = 0.0

if 0 <= power and power < 0.5:
  green = 1.0
  red = 2 * power
if 0.5 <= power and power <= 1:
  red = 1.0
  green = 1.0 - 2 * (power - 0.5)

red = int(red * 255)
green = int(green * 255)
blue = int(blue * 255)

this_cves=int(this_cves)
if this_cves == 0:
  red=0
  green=255
  blue=0
if this_cves > 0 and this_cves <= 10:
  red=255
  green=137
  blue=0
if this_cves > 10 and this_cves <=20:
  red=255
  green=247
  blue=0
if this_cves > 20:
  red=213
  green=255
  blue=0

print('#'+format(red, '02x')+format(green, '02x')+format(blue, '02x'))
