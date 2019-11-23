#!/bin/bash

export LZLOAD_LIB="libidn2.so.0:libunistring.so.2:libacl.so.1:libtestlookup.so.0:libattr.so.1:libz.so.1:libpam.so.0:libpamc.so.0:libpam_misc.so.0:libcrypto.so.1.1:libssl.so.1.1:libapt-pkg.so.5.0:libapt-private.so.0.0:libapt-inst.so.2.0:libgcrypt.so.20:libgpg-error.so.0:liblzma.so.5:libgmp.so.10:libcom_err.so.2:libss.so.2:libe2p.so.2:libext2fs.so.2:libnettle.so.6:libhogweed.so.4:libpcre32.so.3:libpcre.so.3:libpcre16.so.3:libpcreposix.so.3:libpcrecpp.so.0:libudev.so.1:libsystemd.so.0:libnss_myhostname.so.2:libnss_resolve.so.2:libnss_systemd.so.2:libnss_mymachines.so.2:liblber-2.4.so.2:libldap-2.4.so.2:libldap_r-2.4.so.2:libslapi-2.4.so.2:libcurl.so.4:libssh2.so.1:libcap-ng.so.0:librtmp.so.1:libgnutls-openssl.so.27:libgnutls-dane.so.0:libgnutlsxx.so.28:libgnutls.so.30:libtasn1.so.6:libkdb_ldap.so.1:libdb.so.1:libkrb5support.so.0:libprofile.so.1:libkdb5.so.9:libk5crypto.so.3:libkrb5.so.3:libgssapi_krb5.so.2:libgssrpc.so.4:libkadm5clnt_mit.so.11:libkadm5srv_mit.so.11:libkrad.so.0:libbz2.so.1.0:libsepol.so.1:liblz4.so.1:libffi.so.6:libotp.so.2:libntlm.so.2:libgs2.so.2:libsasldb.so.2:liblogin.so.2:libplain.so.2:libanonymous.so.2:libldapdb.so.2:libcrammd5.so.2:libsql.so.2:libgssapiv2.so.2:libscram.so.2:libdigestmd5.so.2:libsasl2.so.2:libseccomp.so.2:libpsl.so.5:libnghttp2.so.14:libsemanage.so.1:libp11-kit.so.0:"

# Path points to the real libraries
export LZ_LIBRARY_PATH="../srcs/curl/mod-lib:../srcs/curl/mod-lib/lib/x86_64-linux-gnu:../srcs/curl/mod-lib/usr/lib/x86_64-linux-gnu:../srcs/curl/mod-lib/usr/lib32:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu/"

# Path points to our lzload and fake libraries
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:../srcs/curl/lib"

curl google.com

