#!/bin/bash

#export LZLOAD_LIB="libcrypto.so.1.1:libidn2.so.0:libpcre.so.3:libpsl.so.5:libssl.so.1.1"
export LZLOAD_LIB="libidn2.so.0:libpsl.so.5:libunistring.so.2"

# Path points to the real libraries
export LZ_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/"

# Path points to our lzload and fake libraries
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:./src-out/lib"

wget google.com

wget https://ftp.gnu.org/gnu/wget/wget-1.20.tar.gz

wget http://www.köln.de


