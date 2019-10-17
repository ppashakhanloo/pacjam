#!/bin/bash

apt-get install -y debhelper
apt-get install -y bear

sudo mv /usr/bin/make /usr/bin/make-orig
cp aux/make /usr/bin/
cp aux/buildflags.conf /etc/dpkg/
