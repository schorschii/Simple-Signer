#!/usr/bin/env python3
# *-* coding: utf-8 *-*
import sys
import datetime
import subprocess

from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class SimpleSignerAboutWindow(QDialog):
	def __init__(self, *args, **kwargs):
		super(SimpleSignerAboutWindow, self).__init__(*args, **kwargs)
		self.InitUI()

	def InitUI(self):
		self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
		self.buttonBox.accepted.connect(self.accept)

		self.layout = QVBoxLayout(self)

		labelAppName = QLabel(self)
		labelAppName.setText(self.parentWidget().PRODUCT_NAME + " v" + self.parentWidget().PRODUCT_VERSION)
		labelAppName.setStyleSheet("font-weight:bold")
		labelAppName.setAlignment(Qt.AlignCenter)
		self.layout.addWidget(labelAppName)

		labelCopyright = QLabel(self)
		labelCopyright.setText(
			"<br>"
			"© 2021 <a href='https://georg-sieber.de'>Georg Sieber</a>"
			"<br>"
			"<br>"
			"GNU General Public License v3.0"
			"<br>"
			"<a href='"+self.parentWidget().PRODUCT_WEBSITE+"'>"+self.parentWidget().PRODUCT_WEBSITE+"</a>"
			"<br>"
		)
		labelCopyright.setOpenExternalLinks(True)
		labelCopyright.setAlignment(Qt.AlignCenter)
		self.layout.addWidget(labelCopyright)

		labelDescription = QLabel(self)
		labelDescription.setText(
			"""Simple-Signer allows you to to sign PDFs using a simple GUI.\n\n"""
		)
		labelDescription.setStyleSheet("opacity:0.8")
		labelDescription.setFixedWidth(450)
		labelDescription.setWordWrap(True)
		self.layout.addWidget(labelDescription)

		self.layout.addWidget(self.buttonBox)

		self.setLayout(self.layout)
		self.setWindowTitle("About")

class SimpleSignerMainWindow(QMainWindow):
	PRODUCT_NAME      = 'Simple-Signer'
	PRODUCT_VERSION   = '1.0.0'
	PRODUCT_WEBSITE   = 'https://github.com/schorschii/Simple-Signer'

	def __init__(self):
		super(SimpleSignerMainWindow, self).__init__()
		self.InitUI()

	def InitUI(self):
		# Menubar
		mainMenu = self.menuBar()

		# File Menu
		fileMenu = mainMenu.addMenu('&File')

		fileMenu.addSeparator()
		quitAction = QAction('&Quit', self)
		quitAction.setShortcut('Ctrl+Q')
		quitAction.triggered.connect(self.OnQuit)
		fileMenu.addAction(quitAction)

		# Help Menu
		editMenu = mainMenu.addMenu('&Help')

		aboutAction = QAction('&About', self)
		aboutAction.setShortcut('F1')
		aboutAction.triggered.connect(self.OnOpenAboutDialog)
		editMenu.addAction(aboutAction)

		# Window Content
		grid = QGridLayout()

		self.lblPdfPath = QLabel('PDF File')
		grid.addWidget(self.lblPdfPath, 0, 0)
		self.txtPdfPath = QLineEdit()
		grid.addWidget(self.txtPdfPath, 1, 0)
		self.btnSearchPdfPath = QPushButton('Search...')
		self.btnSearchPdfPath.clicked.connect(self.OnClickSearchPdfPath)
		grid.addWidget(self.btnSearchPdfPath, 1, 1)

		self.lblCertPath = QLabel('Certificate File')
		grid.addWidget(self.lblCertPath, 2, 0)
		self.txtCertPath = QLineEdit()
		grid.addWidget(self.txtCertPath, 3, 0)
		self.btnSearchCertPath = QPushButton('Search...')
		self.btnSearchCertPath.clicked.connect(self.OnClickSearchCertPath)
		grid.addWidget(self.btnSearchCertPath, 3, 1)

		self.lblPassword = QLabel('Certificate Password')
		grid.addWidget(self.lblPassword, 4, 0)
		self.txtCertPassword = QLineEdit()
		self.txtCertPassword.setEchoMode(QLineEdit.Password)
		self.txtCertPassword.returnPressed.connect(self.OnReturnPressed)
		grid.addWidget(self.txtCertPassword, 5, 0)

		self.btnSign = QPushButton('Sign!')
		#self.btnSign.setEnabled(False)
		self.btnSign.clicked.connect(self.OnClickSign)
		grid.addWidget(self.btnSign, 6, 0)

		widget = QWidget(self)
		widget.setLayout(grid)
		self.setCentralWidget(widget)
		self.txtCertPassword.setFocus()

		# Window Settings
		self.setMinimumSize(400, 200)
		self.setWindowTitle(self.PRODUCT_NAME+' v'+self.PRODUCT_VERSION)

		# Defaults
		if len(sys.argv) > 1: self.txtPdfPath.setText(sys.argv[1])
		if len(sys.argv) > 2: self.txtCertPath.setText(sys.argv[2])

	def OnQuit(self, e):
		sys.exit()

	def OnOpenAboutDialog(self, e):
		dlg = SimpleSignerAboutWindow(self)
		dlg.exec_()

	def OnClickSearchPdfPath(self, e):
		fileName, _ = QFileDialog.getOpenFileName(self, "Choose PDF File", None, "PDF Files (*.pdf);;All Files (*.*)")
		if(fileName): self.txtPdfPath.setText(fileName)

	def OnClickSearchCertPath(self, e):
		fileName, _ = QFileDialog.getOpenFileName(self, "Choose Certificate File", None, "Certificate Files (*.p12);;All Files (*.*)")
		if(fileName): self.txtCertPath.setText(fileName)

	def OnClickOpenSigned(self, e):
		cmd = ['libreoffice', self.getSignedPdfFileName()]
		res = subprocess.run(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, universal_newlines=True)
		if res.returncode != 0: raise Exception(' '.join(cmd)+' returned non-zero exit code '+str(res.returncode))

	def OnReturnPressed(self):
		self.OnClickSign(None)

	def OnClickSign(self, e):
		try:
			strDate = (datetime.datetime.utcnow() - datetime.timedelta(hours=12)).strftime("D:%Y%m%d%H%M%S+00'00'")
			dct = {
				"aligned": 0,
				"sigflags": 3,
				"sigflagsft": 132,
				"sigpage": 0,
				"sigbutton": False,
				"sigfield": "Signature"+strDate,
				"auto_sigfield": False,
				"sigandcertify": True,
				"signaturebox": (470, 840, 570, 640),
				"signature": "",
				#"signature_img": "signature_test.png",
				"contact": "",
				"location": "",
				"signingdate": strDate,
				"reason": "",
				"password": "",
			}
			certData = open(self.txtCertPath.text(), "rb").read()
			p12Data = pkcs12.load_key_and_certificates(certData, str.encode(self.txtCertPassword.text()), backends.default_backend())
			pdfData = open(self.txtPdfPath.text(), "rb").read()
			signData = cms.sign(pdfData, dct, p12Data[0], p12Data[1], p12Data[2], "sha256")
			with open(self.getSignedPdfFileName(), "wb") as fp:
				fp.write(pdfData)
				fp.write(signData)
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Information)
				msg.setWindowTitle('😇')
				msg.setText('Signed successfully as »'+self.getSignedPdfFileName()+'«.')
				msg.setStandardButtons(QMessageBox.Ok)
				btnOpen = msg.addButton('Open With LibreOffice', QMessageBox.ActionRole)
				btnOpen.clicked.connect(self.OnClickOpenSigned)
				retval = msg.exec_()

		except Exception as e:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setWindowTitle('😕')
			msg.setText(str(e))
			msg.setStandardButtons(QMessageBox.Ok)
			retval = msg.exec_()

	def getSignedPdfFileName(self):
		return self.txtPdfPath.text().replace(".pdf", "-signed.pdf")

def main():
	app = QApplication(sys.argv)
	window = SimpleSignerMainWindow()
	window.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
