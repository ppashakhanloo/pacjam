#!/bin/bash

debian_dist_names=("buster" "stretch" "jessie" "wheezy" "squeeze")
debian_dist_contents=("" "" "" "" "")

declare -A debian_dists 

debian_dists["buster2019"]="http://ftp.debian.org/debian/dists/buster/main/binary-amd64/Packages.gz"
debian_dists["stretch2017"]="http://ftp.debian.org/debian/dists/stretch/main/binary-amd64/Packages.gz"
debian_dists["jessie2015"]="http://ftp.debian.org/debian/dists/jessie/main/binary-amd64/Packages.gz"
debian_dists["wheezy2013"]="http://archive.debian.org/debian-archive/debian/dists/wheezy/main/binary-amd64/Packages.gz"
debian_dists["squeeze2011"]="http://archive.debian.org/debian-archive/debian/dists/squeeze/main/binary-amd64/Packages.gz"


# retrieve package lists
for key in ${!debian_dists[@]}; do
    wget -q ${debian_dists[${key}]}
    gunzip Packages.gz
    mv Packages Packages-${key}
    echo "Downloaded" ${key} ${debian_dists[${key}]}
done


# retrieve version info
for key in ${!debian_dists[@]}; do
  cat Packages-${key} | grep -E 'Package:|Version:' > Package-Versions-${key}
  sed -i 's/Version: /,/g' Package-Versions-${key}
  sed -i 's/Package: //g' Package-Versions-${key}
  sed -i 'N;s/\n//' Package-Versions-${key}
  echo "Processed" ${key}
done

