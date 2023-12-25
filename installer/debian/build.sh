#!/bin/bash
set -e

# build .deb package

LANG=C dpkg-buildpackage -us -uc -b
