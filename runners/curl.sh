#!/bin/bash

export LZLOAD_LIB="libcrypto.so.1.1:libssl.so.1.1:libacl.so.1:libtestlookup.so.0:libattr.so.1:libz.so.1:libgpg-error.so.0:libgmp.so.10:libcom_err.so.2.1:libss.so.2.0:libe2p.so.2.3:libext2fs.so.2.4:libffi.so.6:liblzma.so.5:libpcre.so.3:libpcre16.so.3:libpcre32.so.3:libpcreposix.so.3:libpcrecpp.so.0:libcurl.so.4:libssh2.so.1:libgnutls-openssl.so.27:libgnutls-dane.so.0:libgnutls.so.30:libgnutlsxx.so.28:libtasn1.so.6:librtmp.so.1:libnettle.so.6:libhogweed.so.4:libkdb_ldap.so.1.0:libdb.so.1.1:libkrb5support.so.0.1:libprofile.so.1.1:libkdb5.so.9.0:libk5crypto.so.3.1:libkrb5.so.3.3:libgssapi_krb5.so.2.2:libgssrpc.so.4.2:libkadm5clnt_mit.so.11.0:libkadm5srv_mit.so.11.0:libkrad.so.0.0:libkeyutils.so.1.8:libbz2.so.1:libunistring.so.2:libpsl.so.5:libidn2.so.0:libp11-kit.so.0:libnghttp2.so.14:libotp.so.2:libdigestmd5.so.2:libsql.so.2:libgs2.so.2:libscram.so.2:libanonymous.so.2:liblogin.so.2:libplain.so.2:libsasldb.so.2:libcrammd5.so.2:libldapdb.so.2:libgssapiv2.so.2:libntlm.so.2:libsasl2.so.2:"

# Path points to the real libraries
export LZ_LIBRARY_PATH="/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu/"

# Path points to our lzload and fake libraries
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:../srcs/curl/lib"

curl google.com

