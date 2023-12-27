#!/bin/bash
set -e

# build .deb package

# check root permissions
if [ "$EUID" -ne 0 ] && ! groups | grep -q sudo ; then
    echo "Please run this script as root!"
    #exit 1 # disabled for github workflow. don't know why this check fails here but sudo works.
fi

# cd to working dir
cd "$(dirname "$0")"

# compile language files
make -C ../..

# empty / create necessary directories
if [ -d "simple-signer/usr" ]; then
    sudo rm -r simple-signer/usr
fi

# copy files in place
sudo install -D -m 644 ../../assets/simple-signer.desktop      -t simple-signer/usr/share/applications
sudo install -D -m 644 ../../assets/simple-signer.nemo_action  -t simple-signer/usr/share/nemo/actions
sudo install -D -m 644 ../../lang/*.qm                         -t simple-signer/usr/share/simple-signer/lang
sudo install -D -m 644 ../../simple_signer/*.py                -t simple-signer/usr/share/simple-signer/simple_signer
sudo install -D -m 644 ../../requirements.txt                  -t simple-signer/usr/share/simple-signer
sudo install -D -m 644 ../../setup.py                          -t simple-signer/usr/share/simple-signer
sudo install -D -m 644 ../../README.md                         -t simple-signer/usr/share/simple-signer

sudo mkdir -p simple-signer/usr/bin
sudo ln -sf   /usr/share/simple-signer/venv/bin/simple-signer     simple-signer/usr/bin/simple-signer

# build deb
dpkg-deb -Zxz --build simple-signer

echo "Build finished"
