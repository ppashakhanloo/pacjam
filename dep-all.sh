#!/bin/bash

LZLOAD_PATH=$HOME/var/lib/lzload

if [ "$#" -ne 3 ]; then
  echo "$0 usage: [PACKAGE NAME] [BUILD-DIR]"
  exit 1
fi

package=$1
builddir=$2

# 1. Generate a dependency list for package
./dep-find.py -p $package

# 2. Populate the LZLOAD symbol repository
./dep-symbol.py -d $LZLOAD_PATH/symbol-out ${pacakge}.dep

# 3. Build package dependencies
./dep-src.py -d $builddir ${pacakge}.dep
