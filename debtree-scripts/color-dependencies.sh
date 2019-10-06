#!/bin/bash

./debtree --arch=amd64 --no-alternatives --no-provides --no-conflicts --no-versions "$1" > a.dot

grep -o '".*"' a.dot | sed 's/->/\n/g'  | sed 's/"//g' | sed 's/\[.*//' | sed 's/\:.*//' | sed 's/[ \t]*$//' | sed 's/^[ \t]*//' | sort -u > package-list

sed 's/$/,0/g' package-list > package-list-versioned

first=$(awk '/->/ { ln = FNR } END { print ln }' a.dot)
first=$((first+1))

last=$(awk '/}/ { ln = FNR } END { print ln }' a.dot)
last=$((last-1))

sed -e "${first},${last}d" a.dot > b.dot

rm -f cves
touch cves
while IFS=, read -r package version
do
  echo $package
  cve=$(echo "$package,$version" | ./../debsecan/src/debsecan | sed -n 5p) 
  echo $cve >> cves
done < package-list-versioned

cve_list=()
cves_total=0
while read line; do
  cve_list+=($line)
  cves_total=$((cves_total+line))
done < cves

package_list=()
while read line; do
  echo "$line"
  package_list+=($line)
done < package-list

index=0
for package in "${package_list[@]}"
do
  curr_cves="${cve_list[$index]}"
  index=$((index+1))
  color=`echo "$curr_cves $cves_total" | python3 color.py`
  pos=$((first+j))
  sed -e "${pos}i\"$package\" [style=filled,fillcolor=\"$color\"];" b.dot > c.dot
  mv c.dot b.dot
done
