#!/bin/bash

export LZLOAD_LIB="libacl.so.1:libtestlookup.so.0:libattr.so.1:libz.so.1:libncurses.so.6.1:libpanel.so.6.1:libmenu.so.6.1:libform.so.6.1:libtinfo.so.6.1:libreadline.so.7.0:libhistory.so.7.0:liblzma.so.5:libpcre.so.3:libpcre16.so.3:libpcre32.so.3:libpcreposix.so.3:libpcrecpp.so.0:libbz2.so.1:"

# Path points to the real libraries
export LZ_LIBRARY_PATH="/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu/"

# Path points to our lzload and fake libraries
export LD_LIBRARY_PATH="$HOME/lzload/build:../srcs/bc/lib"

echo $LD_LIBRARY_PATH

bc -i
