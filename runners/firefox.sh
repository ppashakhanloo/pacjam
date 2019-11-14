#!/bin/bash

export LZLOAD_LIB="libasound.so.2:libcairo.so.2:libcairo-gobject.so.2:libcairo-script-interpreter.so.2:libdbus-1.so.3:libdbus-glib-1.so.2:libevent_pthreads-2.1.so.6:libevent_openssl-2.1.so.6:libevent_core-2.1.so.6:libevent_extra-2.1.so.6:libevent-2.1.so.6:libffi.so.6:libfontconfig.so.1:libfreetype.so.6:libgio-2.0.so.0:libglib-2.0.so.0:libgmodule-2.0.so.0:libgobject-2.0.so.0:libgthread-2.0.so.0:libgdk-3.so.0:libhunspell-1.7.so.0:libjsoncpp.so.1:libpangoft2-1.0.so.0:libpangocairo-1.0.so.0:libpangoxft-1.0.so.0:libpango-1.0.so.0:libstartup-notification-1.so.0:libvpx.so.5:libX11.so.6:libX11-xcb.so.1:libxcb-randr.so.0:libxcb-xinerama.so.0:libxcb-xvmc.so.0:libxcb-dri3.so.0:libxcb-shape.so.0:libxcb-glx.so.0:libxcb-shm.so.0:libxcb-xfixes.so.0:libxcb-xf86dri.so.0:libxcb-dpms.so.0:libxcb-xkb.so.1:libxcb-render.so.0:libxcb.so.1:libxcb-record.so.0:libxcb-sync.so.1:libxcb-xv.so.0:libxcb-dri2.so.0:libxcb-composite.so.0:libxcb-present.so.0:libxcb-screensaver.so.0:libxcb-damage.so.0:libxcb-res.so.0:libxcb-xtest.so.0:libxcb-xinput.so.0:libXcomposite.so.1:libXdamage.so.1:libXext.so.6:libXfixes.so.3:libXrender.so.1:libz.so.1:libprocps.so.7:"

# Path points to the real libraries
export LZ_LIBRARY_PATH="../srcs/firefox-dir/mod-lib:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu/"

# Path points to our lzload and fake libraries
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:../srcs/firefox-dir/lib"

firefox-esr -headless --screenshot http://google.com
