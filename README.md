# Simple Signer
Simple Signer allows you to sign PDF files using a simple GUI.

![Screenshot](.github/screenshot.png)

## But why?
On current Ubuntu versions, it is not possible to import personal certificates into the certificate management application called "Seahorse" (see [here](https://gitlab.gnome.org/GNOME/seahorse/-/issues/232)). This prevents LibreOffice from signing PDF documents. That's why I created this workaround.

As additional feature, Simple Signer allows you to draw stamps corresponding to your signature as known from the Adobe Reader.

## Installation
### Debian Package
You can download and install the `.deb` package from the [latest release](https://github.com/schorschii/Simple-Signer/releases) on GitHub.

### Manual Installation
```
apt install python3-pip python3-pyqt5 swig
(sudo -H) pip3 install endesive PyMuPDF

# copy simple-signer.py to /usr/bin/simple-signer
# copy simple-signer.desktop into /usr/local/share/applications

sudo update-desktop-database
```

## Usage
- Start the script and choose PDF and cert file using the buttons in the GUI.

or

- Right-click on a PDF file in your file manager -> "Open With" -> "Simple Signer".

then

- Enter the path to your certificate file and your certificate's passphrase, then click:
  - **Sign**: allows multiple users to place their signature
  - **Certify**: places your signature and locks the document - after that, no further signature can be added
  - **Draw Stamp**: you can optionally place a visual stamp on the document which is linked to your signature

## Advanced Usage / Signature Customization
You can add the following (additional) settings to the config file `~/.config/Simple-Signer/settings.ini`:
```
[settings]
cert-path = /path/to/my/cert.p12
stamp-path = 
draw-stamp = 1

signature-contact = Schorschii
signature-location = Sieber Systems HQ
signature-reason = Weils geht!
stamp-background = 255,255,255
stamp-outline = 255,0,0
stamp-border = 2
stamp-labels = CN,DN,date,contact,reason,location
```

## Development
### I18n
```
# 1. Create translation files from code
pylupdate5 simple-signer.py -ts lang/de.ts

# 2. Use Qt Linguist to translate the file

# 3. Compile translation files for usage
lrelease lang/de.ts
```
