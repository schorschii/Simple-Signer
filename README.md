# Simple Signer
Simple Signer allows you to sign PDF files using a simple GUI.

## But why?
On current Ubuntu versions, it is not possible to import personal certificates into the certificate management application called "Seahorse" (see [here](https://gitlab.gnome.org/GNOME/seahorse/-/issues/232)). This prevents LibreOffice from signing PDF documents. That's why I created this workaround.

## Installation
```
apt install python3-pip python3-pyqt5 swig
pip3 install endesive

# move simple-signer.py into /usr/bin/simple-signer
# move simple-signer.nemo_action into /usr/local/share/nemo/actions
# move simple-signer.desktop into /usr/local/share/applications
```

## Usage
- Start the script and choose PDF and cert file using the buttons in the GUI.

or

- Right-click on a PDF file in Nemo file manager and select "Sign PDF" -> Simple Signer GUI will appear.

then

- Enter the path to your certificate file and your certificate's passphrase, then click "Sign!"

## Development
### I18n
```
# 1. Create translation files from code
pylupdate5 simple-signer.py -ts lang/de.ts

# 2. Use Qt Linguist to translate the file

# 3. Compile translation files for usage
lrelease lang/de.ts
```
