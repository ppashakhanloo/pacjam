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
  # remove invalid instances
  sed -i '/-Package/ d' Package-Versions-${key}
  sed -i '/-Version/ d' Package-Versions-${key}
  sed -i '/Version::/ d' Package-Versions-${key}
  sed -i '/wvVersion/ d' Package-Versions-${key}
  sed -i '/\"Package/ d' Package-Versions-${key}
  sed -i '/::Version/ d' Package-Versions-${key}
  sed -i '/Package::/ d' Package-Versions-${key}
  
  # transform to comma-separated csv file
  sed -i 's/Version: /,/g' Package-Versions-${key}
  sed -i 's/Package: //g' Package-Versions-${key}
  sed -i 'N;s/\n//' Package-Versions-${key}
  echo "Processed" ${key}
done

# retrieve CVEs
for key in ${!debian_dists[@]}; do
  cat Package-Versions-${key} | ./debsecan > CVE-List-${key}
  sed -i 's/$/,/g' CVE-List-${key}
  sed -i 'N;N;N;N;s/\n//g' CVE-List-${key}
  cut -d, -f3 --complement CVE-List-${key} > temp
  cut -d, -f5 --complement temp > CVE-List-${key}
  rm -f temp
  echo "Retrieved CVEs from"  ${key}
done

# join popcon data with CVE
for key in ${!debian_dists[@]}; do
  sort -t, -k1,1 CVE-List-${key} > file1
  sort -t, -k2,2 popcon_by_inst.csv > file2
  join -1 1 -2 2 -t, file1 file2 > FULL-${key}
  rm -f file1 file2
  #sed -i '1s/^/package,version,cve-list,cve-num,popcon-rank,inst,vote,old,recent,no-file\n/' FULL-${key}
  echo "Joined CVEs with popcon data for"  ${key}
done
