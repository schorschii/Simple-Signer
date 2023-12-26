#!/bin/bash
set -e

# build the .deb package

LANG=C dpkg-buildpackage --no-sign --build=binary
