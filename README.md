# Simple-Signer
Simple Signer allows you to sign PDF files using a simple GUI.

## But why?
On current Ubuntu versions, it is not possible to import personal certificates into the certificate management application called "Seahorse" (see [here](https://gitlab.gnome.org/GNOME/seahorse/-/issues/232)). This prevents LibreOffice from signing PDF documents. That's why I created this workaround.

## Installation
```
apt install python3-pyqt5
pip3 install endesive

# move simple-signer.py and simple-signer.nemo_action into ~/.local/share/nemo/actions
```

## Usage
- Start the script and choose PDF and cert file using the buttons in the GUI.

or

- Right-click on a PDF file in Nemo file manager and select "Sign PDF" -> Simple Signer GUI will appear.

then

- Enter your certificate's passphrase and click "Sign!"
