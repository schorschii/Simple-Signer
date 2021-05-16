#!/usr/bin/env python3
# *-* coding: utf-8 *-*

import sys, os
import datetime
import subprocess
import configparser
from pathlib import Path
from shutil import which

from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms

if os.environ.get("QT_QPA_PLATFORMTHEME") == "qt5ct":
	os.environ["QT_QPA_PLATFORMTHEME"] = "gtk2"
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
		#labelDescription.setFixedWidth(400)
		labelDescription.setWordWrap(True)
		self.layout.addWidget(labelDescription)

		self.layout.addWidget(self.buttonBox)

		self.setLayout(self.layout)
		self.setWindowTitle("About")

class SimpleSignerMainWindow(QMainWindow):
	PRODUCT_NAME      = 'Simple Signer'
	PRODUCT_VERSION   = '1.2.0'
	PRODUCT_WEBSITE   = 'https://github.com/schorschii/Simple-Signer'

	configPath = str(Path.home())+'/.simple-signer.ini'

	def __init__(self):
		super(SimpleSignerMainWindow, self).__init__()
		self.InitUI()

	def InitUI(self):
		# Menubar
		mainMenu = self.menuBar()

		# File Menu
		fileMenu = mainMenu.addMenu('&File')
		signAction = QAction('&Sign', self)
		signAction.setShortcut('Ctrl+S')
		signAction.triggered.connect(self.OnClickSign)
		fileMenu.addAction(signAction)
		fileMenu.addSeparator()
		searchPdfAction = QAction('&Search PDF File...', self)
		searchPdfAction.setShortcut('Ctrl+P')
		searchPdfAction.triggered.connect(self.OnClickSearchPdfPath)
		fileMenu.addAction(searchPdfAction)
		searchCertificateAction = QAction('&Search Certificate File...', self)
		searchCertificateAction.setShortcut('Ctrl+O')
		searchCertificateAction.triggered.connect(self.OnClickSearchCertPath)
		fileMenu.addAction(searchCertificateAction)
		fileMenu.addSeparator()
		quitAction = QAction('&Quit', self)
		quitAction.setShortcut('Ctrl+Q')
		quitAction.triggered.connect(self.close)
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
		boldFont = QFont()
		boldFont.setBold(True)
		self.btnSign.setFont(boldFont)
		self.btnSign.clicked.connect(self.OnClickSign)
		grid.addWidget(self.btnSign, 6, 0)

		widget = QWidget(self)
		widget.setLayout(grid)
		self.setCentralWidget(widget)
		self.txtCertPassword.setFocus()

		# Window Settings
		self.setMinimumSize(400, 200)
		self.setWindowTitle(self.PRODUCT_NAME+' v'+self.PRODUCT_VERSION)

		# Defaults From Config File
		if os.path.exists(self.configPath):
			config = configparser.ConfigParser()
			config.read(self.configPath)
			self.txtCertPath.setText(config['settings']['cert-path'])

		# Defaults From Command Line
		if len(sys.argv) > 1: self.txtPdfPath.setText(sys.argv[1])
		if len(sys.argv) > 2: self.txtCertPath.setText(sys.argv[2])

	def closeEvent(self, event):
		# Write Settings To File
		config = configparser.ConfigParser()
		config.add_section('settings')
		config['settings']['cert-path'] = self.txtCertPath.text()
		with open(self.configPath, 'w') as configfile:
			config.write(configfile)
		event.accept()

	def OnOpenAboutDialog(self, e):
		dlg = SimpleSignerAboutWindow(self)
		dlg.exec_()

	def OnClickSearchPdfPath(self, e):
		fileName = self.OpenFileDialog("Choose PDF File", "PDF Files (*.pdf);;All Files (*.*)")
		if fileName: self.txtPdfPath.setText(fileName)

	def OnClickSearchCertPath(self, e):
		fileName = self.OpenFileDialog("Choose Certificate File", "Certificate Files (*.p12);;All Files (*.*)")
		if fileName: self.txtCertPath.setText(fileName)

	def OpenFileDialog(self, title, filter):
		fileName, _ = QFileDialog.getOpenFileName(self, title, None, filter)
		return fileName

	def OnClickOpenSigned(self, e):
		if self.existsBinary('okular'): # Okular displays signatures
			cmd = ['okular', self.getSignedPdfFileName()]
		elif self.existsBinary('libreoffice'): # LibreOffice displays signatures
			cmd = ['libreoffice', self.getSignedPdfFileName()]
		elif self.existsBinary('xdg-open'): # Linux fallback
			cmd = ['xdg-open', self.getSignedPdfFileName()]
		elif self.existsBinary('open'): # macOS
			cmd = ['open', self.getSignedPdfFileName()]
		res = subprocess.Popen(cmd, start_new_session=True)

	def OnClickOpenSignedInFileManager(self, e):
		if self.existsBinary('nemo'): # Linux Mint
			cmd = ['nemo', self.getSignedPdfFileName()]
		elif self.existsBinary('nautilus'): # Ubuntu
			cmd = ['nautilus', self.getSignedPdfFileName()]
		elif self.existsBinary('nautilus'): # Linux fallback
			cmd = ['xdg-open', os.path.dirname(self.getSignedPdfFileName())]
		elif self.existsBinary('open'): # macOS
			cmd = ['open', os.path.dirname(self.getSignedPdfFileName())]
		res = subprocess.Popen(cmd, start_new_session=True)

	def OnReturnPressed(self):
		self.OnClickSign(None)

	def OnClickSign(self, e):
		try:
			pdfPath = self.txtPdfPath.text()
			signedPdfPath = self.getSignedPdfFileName()
			if pdfPath == signedPdfPath: return

			strDate = (datetime.datetime.utcnow() - datetime.timedelta(hours=12)).strftime("D:%Y%m%d%H%M%S+00'00'")
			dct = {
				"aligned": 0,
				"sigflags": 3,
				"sigflagsft": 132,
				"sigpage": 0,
				"sigbutton": False,
				"sigfield": "Signature-"+str(datetime.datetime.utcnow().timestamp()),
				"auto_sigfield": False,
				"sigandcertify": True,
				"signaturebox": (0, 0, 0, 0),
				"signature": "",
				#"signature_img": "signature_test.png",
				"contact": "",
				"location": "",
				"signingdate": strDate,
				"reason": "",
				#"password": "",
			}
			certData = open(self.txtCertPath.text(), "rb").read()
			p12Data = pkcs12.load_key_and_certificates(certData, str.encode(self.txtCertPassword.text()), backends.default_backend())
			pdfData = open(pdfPath, "rb").read()
			signData = cms.sign(pdfData, dct, p12Data[0], p12Data[1], p12Data[2], "sha256")
			with open(signedPdfPath, "wb") as fp:
				fp.write(pdfData)
				fp.write(signData)
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Information)
				msg.setWindowTitle('😇')
				msg.setText('Successfully signed and saved as »'+signedPdfPath+'«.')
				msg.setStandardButtons(QMessageBox.Ok)
				btnOpen = msg.addButton('Open Directory', QMessageBox.ActionRole)
				btnOpen.clicked.connect(self.OnClickOpenSignedInFileManager)
				btnOpen = msg.addButton('Open Signed PDF', QMessageBox.ActionRole)
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
		originalFileName = self.txtPdfPath.text()
		if originalFileName.lower().endswith(".pdf"):
			return originalFileName[:-4]+"-signed.pdf"
		else:
			return originalFileName+"-signed.pdf"

	def existsBinary(self, name):
		return which(name) is not None

def main():
	app = QApplication(sys.argv)
	window = SimpleSignerMainWindow()
	window.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
