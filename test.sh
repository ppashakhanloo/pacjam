#!/bin/bash

# Simple test script for the dev-symbols tool. Just meant to make sure its use can
# be replicated, and perform some simple regression tests

# Some wget dependencies
# libc6 
# libssl1.1

JQ=/home/acanino/local/bin/jq

rm -rf test/symbol-out
mkdir test/symbol-out
echo "Testing wget deb download "
./dep-symbol.py -d test/symbol-out -o test/dep.out -t test/wget/analysis-out/http.txt test/wget.dep >/dev/null 2>&1

# 1. Check to make sure a few of the dependencies got the symbol information
if [ ! -f test/symbol-out/libc6/symbols ]; then
  echo "FAILED libc symbol test"
  exit 1
fi
if [ ! -f test/symbol-out/libssl1.1/symbols ]; then
  echo "FAILED libssl symbol test"
  exit 1
fi

# 2. Check to see if the trace behaved as expected, should use libc, libunistring, not libssl
echo "Testing wget libc and libunistring use"
b=`cat test/dep.out | ${JQ} '.used|any(.[] ; .package_name == "libc6")'`
if [ $b = false ]; then
  echo "FAILED wget http libc use check"
  exit 1
fi
b=`cat test/dep.out | ${JQ} '.used|any(.[] ; .package_name == "libunistring2")'`
if [ $b = false ]; then
  echo "FAILED wget http libunistring use check"
  exit 1
fi
b=`cat test/dep.out | ${JQ} '.used|any(.[] ; .package_name == "libssl1.1")'`
if [ $b = true ]; then
  echo "FAILED wget http libssl not use check"
  exit 1
fi

./dep-symbol.py -d test/symbol-out -o test/dep.out -t test/wget/analysis-out/ftp.txt test/wget.dep >/dev/null 2>&1
# 3. Give the wget trace that uses libssl a check
echo "Testing wget libssl use"
b=`cat test/dep.out | ${JQ} '.used|any(.[] ; .package_name == "libssl1.1")'`
if [ $b = false ]; then
  echo "FAILED wget ftp libssl use check"
  exit 1
fi

# 4. tar depdencies for symbols to be built for libacl, check
echo "Testing libacl symbol generation"
./dep-symbol.py -d test/symbol-out -o test/dep.out -t test/tar/analysis-out/acl.txt test/coreutils.dep >/dev/null 2>&1
if [ ! -f test/symbol-out/libacl1/symbols ]; then
  echo "FAILED libacl build symbol test"
  exit 1
fi

# 5. Final check that the built symbols can be used to trace the acl trace
echo "Testing tar libacl use"
b=`cat test/dep.out | ${JQ} '.used|any(.[] ; .package_name == "libacl1")'`
if [ $b = false ]; then
  echo "FAILED tar libacl use check"
  exit 1
fi

echo "PASSED all"
