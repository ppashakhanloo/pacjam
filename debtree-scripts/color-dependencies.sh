#!/bin/bash

./debtree --arch=amd64 --no-recommends --no-alternatives --no-provides --no-conflicts --no-versions "$1" > a.dot

grep -o '".*"' a.dot | grep '[-][>]' | sed 's/->/\n/g'  | sed 's/"//g' | sed 's/\[.*//' | sed 's/\:.*//' | sed 's/[ \t]*$//' | sed 's/^[ \t]*//' | sort -u > package-list

sed -i 's/Pr_//g' package-list
sed -i '/^ *$/d' package-list

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

declare -A popcon_inst
declare -A popcon_vote
while IFS=, read -r package inst vote
do
  popcon_inst[$package]=$inst
  popcon_vote[$package]=$vote
done < ALL-CVES

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
  echo "$package"
  echo "${popcon_inst[$package]}"
  echo "${popcon_vote[$package]}"
  
  color=`echo "$curr_cves $cves_total" | python3 color.py`
  
  dummy_inst=${popcon_inst[$package]}
  dummy_vote=${popcon_vote[$package]}
  if [ ! ${popcon_inst[$package]} ] ; then
    dummy_inst=-1
  fi

  if [ ! ${popcon_vote[$package]} ] ; then
    dummy_vote=-1
  fi
  
  border=`echo "$dummy_inst $dummy_vote" | python3 border.py`
  pos=$((first+j))
  sed -e "${pos}i\"$package\" [style=filled,fillcolor=\"$color\",peripheries=\"$border\",shape="oval"];" b.dot > c.dot
  mv c.dot b.dot
done

# draw the dependency graph
dot -Tpng -o images/"$1".png b.dot 
