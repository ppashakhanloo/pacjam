#!/bin/bash

export LZLOAD_LIB="libblkid.so.1:libfdisk.so.1:libffi.so.6:libgmp.so.10:libgnutls-dane.so.0:libgnutls-openssl.so.27:libgnutls.so.30:libgnutlsxx.so.28:libhogweed.so.4:libidn2.so.0:libmount.so.1:libnettle.so.6:libp11-kit.so.0:libpcre2-16.so.0:libpcre2-32.so.0:libpcre2-8.so.0:libpcre2-posix.so.2:libpsl.so.5:libsmartcols.so.1:libtasn1.so.6:libunistring.so.2:libuuid.so.1:libz.so.1"

# Path points to the real libraries
export LZ_LIBRARY_PATH="/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu/"

# Path points to our lzload and fake libraries
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:./src-out/lib"
wget google.com

wget https://ftp.gnu.org/gnu/wget/wget-1.20.tar.gz
