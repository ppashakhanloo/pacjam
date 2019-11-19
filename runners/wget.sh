#!/bin/bash

export LZLOAD_LIB="libz.so.1:libuuid.so.1:libsmartcols.so.1:libblkid.so.1:libmount.so.1:libfdisk.so.1:libgmp.so.10:libffi.so.6:libgnutls-openssl.so.27:libgnutls-dane.so.0:libgnutls.so.30:libgnutlsxx.so.28:libtasn1.so.6:libnettle.so.6:libhogweed.so.4:libunistring.so.2:libpcre2-16.so.0:libpcre2-32.so.0:libpcre2-8.so.0:libpcre2-posix.so.2:libpsl.so.5:libidn2.so.0:libp11-kit.so.0:"

# Path points to the real libraries
export LZ_LIBRARY_PATH="../srcs/wget/mod-lib:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu/"

# Path points to our lzload and fake libraries
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:../srcs/wget/lib"

wget https://ftp.gnu.org/gnu/wget/wget-1.20.tar.gz
