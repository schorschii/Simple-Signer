# Debian Packaging
Architecture Decision Record  
Lang: en  
Encoding: utf-8  
Date: 2023-12-27  
Author: Georg Sieber

## Decision
Debian packages are created using the simple method `dpkg-deb --build` and not with the "official" way using `dpkg-buildpackage` with `dh-virtualenv`.

## Status
Accepted

## Context
The first Debian packages basically just contained `simple-signer.py` with a postinstall script installing the necessary Python modules (which are not available through the Ubuntu/Debian repos) system-wide via `sudo -H pip install ...`. This method stopped working with Debian 12, were pip denies the system-wide module installation beside the system package manager. Although there is a parameter to enforce the installation, it is not a good idea to use this way. There are reasons Debian changed the pip behavior.

The first try was to switch to `dpkg-buildpackage` with the `dh-virtualenv` debhelper creating a .deb package with Python "pre-compiled" venv inside. This method was huge more complex but filly functional implemented in v1.5.1. Unfortunately, those packages now depended on the Python version (the venv has a folder called `lib/python3.10` according to the version of the compiling system). This means that separate packages were necessary to support current Ubuntu and Debian versions (Ubuntu 22.04: Python 3.8, Debian 11: Python 3.9, Ubuntu 22.04: Python 3.10, Debian 12: Python3.11). This is too much overhead for this project and too confusing for end-users.

That's why, a compromise was chosen between both methods. The build stack was switched back to `dpkg-deb --build`. Now, the package's `postinst` script dynamically creates a matching Python venv on the target system while installing. After that, it executes pip to install the necessary libraries inside the newly created venv.

## Consequences
Simple Signer does not use the standard packaging method `dpkg-buildpackage` with the `dh-virtualenv`. The alternative packaging process enables us to have one single package for all Ubuntu/Debian systems with all Python versions. One drawback is that while installing the package, a internet connection is required for pip in order to install the necessary libraries inside the Simple Signer venv.
