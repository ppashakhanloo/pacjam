#!/bin/bash

declare -A debian_dists
debian_dists["buster2019"]="http://ftp.debian.org/debian/dists/buster/main/binary-amd64/Packages.gz"
debian_dists["stretch2017"]="http://ftp.debian.org/debian/dists/stretch/main/binary-amd64/Packages.gz"
debian_dists["jessie2015"]="http://ftp.debian.org/debian/dists/jessie/main/binary-amd64/Packages.gz"
debian_dists["wheezy2013"]="http://archive.debian.org/debian-archive/debian/dists/wheezy/main/binary-amd64/Packages.gz"
debian_dists["squeeze2011"]="http://archive.debian.org/debian-archive/debian/dists/squeeze/main/binary-amd64/Packages.gz"

declare -A popcon_archs
popcon_archs["buster2019"]="buster_popcon_2019_october"
popcon_archs["stretch2017"]="stretch_popcon_2019_july"
popcon_archs["jessie2015"]="jessie_popcon_2017_june"
popcon_archs["wheezy2013"]="wheezy_popcon_2015_april"
popcon_archs["squeeze2011"]="squeeze_popcon_2013_may"


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
  echo "Processed version info for" ${key}
done

# retrieve CVEs
for key in ${!debian_dists[@]}; do
  cat Package-Versions-${key} | ./debsecan > CVE-List-${key}
  sed -i 's/$/,/g' CVE-List-${key}
  sed -i 'N;N;N;N;s/\n//g' CVE-List-${key}
  cut -d, -f3 --complement CVE-List-${key} > temp
  cut -d, -f5 --complement temp > CVE-List-${key}
  rm -f temp
  echo "Retrieved CVEs for" ${key}
done

# join popcon data with each CVE for each dist
for key in ${!debian_dists[@]}; do
  sort -t, -k1,1 CVE-List-${key} > file1
  sort -t, -k1,1 popcon_archive/${popcon_archs[$key]} > file2
  join -1 1 -2 1 -t, file1 file2 > FULL-${key}
  rm -f file1 file2
  sed -i '1s/^/package,version,cve-list,cve-num,inst,vote,old,recent,no-file\n/' FULL-${key}
  echo "Joined CVEs with popcon data for"  ${key}
done

# join popcon data with all dists
cat FULL-buster2019 > temp_popcon
for key in ${!debian_dists[@]}; do
  if [ "${key}" != "buster2019" ]; then
    sort -t, -k1,1 temp_popcon > file1
    sort -t, -k1,1 FULL-${key} > file2
    join -1 1 -2 1 -t, file1 file2 > temp_popcon
    rm -f file1 file2
  fi
#sed -i '1s/^/package,version,cve-list,cve-num,popcon-rank,inst,vote,old,recent,no-file\n/' FULL-${key}
done
mv temp_popcon "ALL-CVES"
echo "Joined all CVEs with popcon data"
