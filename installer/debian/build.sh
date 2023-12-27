#!/bin/bash
set -e

# build .deb package

# check root permissions
if [ "$EUID" -ne 0 ]
    then echo "Please run this script as root!"
    exit 1
fi

# cd to working dir
cd "$(dirname "$0")"

# compile language files
make -C ../..

# empty / create necessary directories
if [ -d "simple-signer/usr" ]; then
    rm -r simple-signer/usr
fi

# copy files in place
install -D -m 644 ../../assets/simple-signer.desktop      -t simple-signer/usr/share/applications
install -D -m 644 ../../assets/simple-signer.nemo_action  -t simple-signer/usr/share/nemo/actions
install -D -m 644 ../../lang/*.qm                         -t simple-signer/usr/share/simple-signer/lang
install -D -m 644 ../../simple_signer/*.py                -t simple-signer/usr/share/simple-signer/simple_signer
install -D -m 644 ../../requirements.txt                  -t simple-signer/usr/share/simple-signer
install -D -m 644 ../../setup.py                          -t simple-signer/usr/share/simple-signer
install -D -m 644 ../../README.md                         -t simple-signer/usr/share/simple-signer

mkdir -p simple-signer/usr/bin
ln -sf   /usr/share/simple-signer/venv/bin/simple-signer     simple-signer/usr/bin/simple-signer

# build deb
dpkg-deb -Zxz --build simple-signer

echo "Build finished"
