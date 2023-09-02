#!/bin/bash
set -e

# build .deb package

# check root permissions
if [ "$EUID" -ne 0 ]
	then echo "Please run this script as root!"
	exit
fi

# cd to working dir
cd "$(dirname "$0")"

# compile language files
lrelease ../../lang/*.ts

# empty / create necessary directories
if [ -d "simple-signer/usr/share/simple-signer" ]; then
	rm -r simple-signer/usr/share/simple-signer
fi
mkdir -p simple-signer/usr/share/simple-signer/lang
mkdir -p simple-signer/usr/share/applications
mkdir -p simple-signer/usr/share/nemo/actions

# copy files in place
cp ../../simple-signer.desktop simple-signer/usr/share/applications
cp ../../simple-signer.nemo_action simple-signer/usr/share/nemo/actions
cp ../../lang/*.qm simple-signer/usr/share/simple-signer/lang
cp ../../simple-signer.py simple-signer/usr/bin/simple-signer

# set file permissions
chown -R root:root simple-signer
chmod 775 simple-signer/usr/bin/simple-signer

# build deb
dpkg-deb -Zxz --build simple-signer

echo "Build finished"
