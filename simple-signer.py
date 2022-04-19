#!/usr/bin/env python3
# *-* coding: utf-8 *-*

import sys, os, io
import datetime
import subprocess
import configparser
from pathlib import Path
from shutil import which

from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms

# gtk2 theme is more convenient when it comes to
# selecting files from network shares using QFileDialog (on linux)
if os.environ.get('QT_QPA_PLATFORMTHEME') == 'qt5ct':
	os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk2'
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from locale import getdefaultlocale


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
			"© 2021-2022 <a href='https://georg-sieber.de'>Georg Sieber</a>"
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
			QApplication.translate('SimpleSigner', 'Simple-Signer allows you to to sign PDFs using a simple user interface.')
			+"\n\n"+
			QApplication.translate('SimpleSigner', 'Signing allows multiple users to place their digital signature on a document.')
			+"\n"+
			QApplication.translate('SimpleSigner', 'Certifiy will place your signature on the document and lock it after that.')
			+"\n"
		)
		labelDescription.setStyleSheet("opacity:0.8")
		#labelDescription.setFixedWidth(400)
		labelDescription.setWordWrap(True)
		self.layout.addWidget(labelDescription)

		self.layout.addWidget(self.buttonBox)

		self.setLayout(self.layout)
		self.setWindowTitle(QApplication.translate('SimpleSigner', 'About'))

class SimpleSignerPreview(QLabel):
	rubberBand = None
	origin = None
	rect = None

	def mousePressEvent(self, event):
		self.origin = event.pos()
		if(self.rubberBand == None): self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
		self.rubberBand.setGeometry(QRect(self.origin, QSize()))
		self.rubberBand.show()

	def mouseMoveEvent(self, event):
		self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

	def mouseReleaseEvent(self, event):
		#self.rubberBand.hide()
		self.rect = QRect(self.origin, event.pos()).normalized()

class SimpleSignerPreviewWindow(QDialog):
	pdfFilePath = None
	pages = []

	stampRect = None
	stampPage = None

	def __init__(self, parent, pdfFilePath):
		super(SimpleSignerPreviewWindow, self).__init__(parent)
		self.pdfFilePath = pdfFilePath

		# Load PDF Preview
		from PIL.ImageQt import ImageQt
		from pdf2image import convert_from_path
		self.pages = convert_from_path(self.pdfFilePath, 60)
		if(len(self.pages) == 0):
			raise Exception(QApplication.translate('SimpleSigner', 'PDF is empty!'))

		self.InitUI()

	def InitUI(self):
		# Window Content
		grid = QGridLayout()

		grid2 = QGridLayout()
		label = QLabel(QApplication.translate('SimpleSigner', 'Page:'))
		grid2.addWidget(label, 0, 0)
		self.sltPage = QComboBox()
		for page in self.pages:
			self.sltPage.addItem(str(self.pages.index(page) + 1))
		self.sltPage.currentIndexChanged.connect(self.OnCurrentIndexChanged)
		grid2.addWidget(self.sltPage, 0, 1)
		grid.addLayout(grid2, 0, 0)

		self.lblPageView = SimpleSignerPreview()
		self.lblPageView.setScaledContents(True)
		self.lblPageView.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
		self.lblPageView.setPixmap(self.pil2pixmap(self.pages[0]))
		grid.addWidget(self.lblPageView, 1, 0)

		self.btnDone = QPushButton(QApplication.translate('SimpleSigner', 'Done'))
		self.btnDone.clicked.connect(self.OnClickDone)
		grid.addWidget(self.btnDone, 2, 0)

		self.setLayout(grid)

		# Window Settings
		self.setMinimumSize(600, 900)
		self.setWindowTitle(QApplication.translate('SimpleSigner', 'Place Stamp'))

	# function to convert python PIL image object to QT pixmap for usage in QT controls
	def pil2pixmap(self, image):
		bytes_img = io.BytesIO()
		image.save(bytes_img, format='JPEG')
		qimg = QImage()
		qimg.loadFromData(bytes_img.getvalue())
		return QPixmap.fromImage(qimg)

	# function to convert coordinate origin from top left (QLabel logic) to bottom left (PDF logic)
	def translateRectCoordinateOrigin(self, rectArray, maxHeight):
		return [
			rectArray[0],
			maxHeight - rectArray[1] - rectArray[3],
			rectArray[0] + rectArray[2],
			maxHeight - rectArray[1]
		]

	# function to scale stamp rect from preview size to real PDF size
	def translateRectToRealSize(self, rectArray, previewWidth, previewHeight, realWidth, realHeight):
		return [
			rectArray[0] * realWidth / previewWidth,
			rectArray[1] * realHeight / previewHeight,
			rectArray[2] * realWidth / previewWidth,
			rectArray[3] * realHeight / previewHeight
		]

	def OnCurrentIndexChanged(self, index):
		self.lblPageView.setPixmap(self.pil2pixmap(self.pages[index]))

	def OnClickDone(self, e):
		if(self.lblPageView.rect == None):
			self.close()
			return

		normalizedRect = self.lblPageView.rect.normalized()
		rect = [ normalizedRect.x(), normalizedRect.y(), normalizedRect.width(), normalizedRect.height() ]

		print([self.lblPageView.width(), self.lblPageView.height()])
		print(rect)
		rect = self.translateRectCoordinateOrigin(rect, self.lblPageView.height())
		print(rect)
		rect = self.translateRectToRealSize(rect, self.lblPageView.width(), self.lblPageView.height(), 595, 840)
		print(rect)

		self.stampPage = self.sltPage.currentIndex()
		self.stampRect = rect
		self.close()

class SimpleSignerMainWindow(QMainWindow):
	PRODUCT_NAME      = 'Simple Signer'
	PRODUCT_VERSION   = '1.3.1'
	PRODUCT_WEBSITE   = 'https://github.com/schorschii/Simple-Signer'

	configPath = str(Path.home())+'/.simple-signer.ini'

	def __init__(self):
		super(SimpleSignerMainWindow, self).__init__()
		self.InitUI()

	def InitUI(self):
		# Menubar
		mainMenu = self.menuBar()

		# File Menu
		fileMenu = mainMenu.addMenu(QApplication.translate('SimpleSigner', '&File'))
		signAction = QAction(QApplication.translate('SimpleSigner', '&Sign'), self)
		signAction.setShortcut('Ctrl+S')
		signAction.triggered.connect(self.OnClickSign)
		fileMenu.addAction(signAction)
		certifyAction = QAction(QApplication.translate('SimpleSigner', '&Certify'), self)
		certifyAction.setShortcut('Ctrl+D')
		certifyAction.triggered.connect(self.OnClickCertify)
		fileMenu.addAction(certifyAction)
		fileMenu.addSeparator()
		choosePdfAction = QAction(QApplication.translate('SimpleSigner', 'Choose &PDF File...'), self)
		choosePdfAction.setShortcut('Ctrl+P')
		choosePdfAction.triggered.connect(self.OnClickChoosePdfPath)
		fileMenu.addAction(choosePdfAction)
		chooseCertificateAction = QAction(QApplication.translate('SimpleSigner', 'Choose C&ertificate File...'), self)
		chooseCertificateAction.setShortcut('Ctrl+O')
		chooseCertificateAction.triggered.connect(self.OnClickChooseCertPath)
		fileMenu.addAction(chooseCertificateAction)
		fileMenu.addSeparator()
		quitAction = QAction(QApplication.translate('SimpleSigner', '&Quit'), self)
		quitAction.setShortcut('Ctrl+Q')
		quitAction.triggered.connect(self.close)
		fileMenu.addAction(quitAction)

		# Help Menu
		editMenu = mainMenu.addMenu(QApplication.translate('SimpleSigner', '&Help'))

		aboutAction = QAction(QApplication.translate('SimpleSigner', '&About'), self)
		aboutAction.setShortcut('F1')
		aboutAction.triggered.connect(self.OnOpenAboutDialog)
		editMenu.addAction(aboutAction)

		# Window Content
		grid = QGridLayout()

		self.lblPdfPath = QLabel(QApplication.translate('SimpleSigner', 'PDF File'))
		grid.addWidget(self.lblPdfPath, 0, 0)
		self.txtPdfPath = QLineEdit()
		grid.addWidget(self.txtPdfPath, 1, 0)
		self.btnChoosePdfPath = QPushButton(QApplication.translate('SimpleSigner', 'Choose...'))
		self.btnChoosePdfPath.clicked.connect(self.OnClickChoosePdfPath)
		grid.addWidget(self.btnChoosePdfPath, 1, 1)

		self.lblCertPath = QLabel(QApplication.translate('SimpleSigner', 'Certificate File'))
		grid.addWidget(self.lblCertPath, 2, 0)
		self.txtCertPath = QLineEdit()
		grid.addWidget(self.txtCertPath, 3, 0)
		self.btnChooseCertPath = QPushButton(QApplication.translate('SimpleSigner', 'Choose...'))
		self.btnChooseCertPath.clicked.connect(self.OnClickChooseCertPath)
		grid.addWidget(self.btnChooseCertPath, 3, 1)

		self.lblPassword = QLabel(QApplication.translate('SimpleSigner', 'Certificate Password'))
		grid.addWidget(self.lblPassword, 4, 0)
		self.txtCertPassword = QLineEdit()
		self.txtCertPassword.setEchoMode(QLineEdit.Password)
		self.txtCertPassword.returnPressed.connect(self.OnReturnPressed)
		grid.addWidget(self.txtCertPassword, 5, 0)

		self.chkDrawStamp = QCheckBox(QApplication.translate('SimpleSigner', 'Draw Stamp'))
		grid.addWidget(self.chkDrawStamp, 6, 0)
		self.txtStampPath = QLineEdit()
		self.txtStampPath.setPlaceholderText(QApplication.translate('SimpleSigner', '(optional)'))
		grid.addWidget(self.txtStampPath, 7, 0)
		self.btnChooseStampPath = QPushButton(QApplication.translate('SimpleSigner', 'Choose...'))
		self.btnChooseStampPath.clicked.connect(self.OnClickChooseStampPath)
		grid.addWidget(self.btnChooseStampPath, 7, 1)

		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setFrameShadow(QFrame.Sunken)
		grid.addWidget(line, 8, 0)

		grid2 = QGridLayout()

		self.btnSign = QPushButton(QApplication.translate('SimpleSigner', 'Sign'))
		self.btnSign.setToolTip(QApplication.translate('SimpleSigner', 'Signing allows multiple users to place their digital signature on a document.'));
		boldFont = QFont()
		boldFont.setBold(True)
		self.btnSign.setFont(boldFont)
		self.btnSign.clicked.connect(self.OnClickSign)
		grid2.addWidget(self.btnSign, 0, 0)

		self.btnCertfiy = QPushButton(QApplication.translate('SimpleSigner', 'Certify'))
		self.btnCertfiy.setToolTip(QApplication.translate('SimpleSigner', 'Certifiy will place your signature on the document and lock it after that.'));
		boldFont = QFont()
		boldFont.setBold(True)
		self.btnCertfiy.setFont(boldFont)
		self.btnCertfiy.clicked.connect(self.OnClickCertify)
		grid2.addWidget(self.btnCertfiy, 0, 1)

		grid.addLayout(grid2, 9, 0)

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
			if('cert-path' in config['settings']): self.txtCertPath.setText(config['settings']['cert-path'])
			if('stamp-path' in config['settings']): self.txtStampPath.setText(config['settings']['stamp-path'])
			if('draw-stamp' in config['settings']): self.chkDrawStamp.setChecked(True if config['settings']['draw-stamp']=='1' else False)

		# Defaults From Command Line
		if len(sys.argv) > 1: self.txtPdfPath.setText(sys.argv[1])
		if len(sys.argv) > 2: self.txtCertPath.setText(sys.argv[2])

	def closeEvent(self, event):
		# Write Settings To File
		config = configparser.ConfigParser()
		config.add_section('settings')
		config['settings']['cert-path'] = self.txtCertPath.text()
		config['settings']['stamp-path'] = self.txtStampPath.text()
		config['settings']['draw-stamp'] = '1' if self.chkDrawStamp.isChecked() else '0'
		with open(self.configPath, 'w') as configfile:
			config.write(configfile)
		event.accept()

	def OnOpenAboutDialog(self, e):
		dlg = SimpleSignerAboutWindow(self)
		dlg.exec_()

	def OnClickChoosePdfPath(self, e):
		fileName = self.OpenFileDialog(QApplication.translate('SimpleSigner', 'PDF File'), 'PDF Files (*.pdf);;All Files (*.*)')
		if fileName: self.txtPdfPath.setText(fileName)

	def OnClickChooseCertPath(self, e):
		fileName = self.OpenFileDialog(QApplication.translate('SimpleSigner', 'Certificate File'), 'Certificate Files (*.p12);;All Files (*.*)')
		if fileName: self.txtCertPath.setText(fileName)

	def OnClickChooseStampPath(self, e):
		fileName = self.OpenFileDialog(QApplication.translate('SimpleSigner', 'Stamp Image File'), 'Image Files (*.jpg *.png);;All Files (*.*)')
		if fileName: self.txtStampPath.setText(fileName)

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
		self.Sign(False)

	def OnClickCertify(self, e):
		self.Sign(True)

	def Sign(self, certify):
		try:
			# get/compile paths
			pdfPath = self.txtPdfPath.text()
			signedPdfPath = self.getSignedPdfFileName()
			if(os.path.exists(signedPdfPath)):
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setWindowTitle(QApplication.translate('SimpleSigner', 'File Warning'))
				msg.setText(QApplication.translate('SimpleSigner', 'The target file »%s« already exists. Continue?') % signedPdfPath)
				msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
				if(msg.exec_() == QMessageBox.Cancel): return

			# compile sign options
			strDate = (datetime.datetime.utcnow() - datetime.timedelta(hours=12)).strftime("D:%Y%m%d%H%M%S+00'00'")
			dct = {
				'aligned': 0,
				'sigflags': 3,
				'sigflagsft': 132,
				'sigpage': 0,
				'sigbutton': False,
				'sigfield': 'Signature-'+str(datetime.datetime.utcnow().timestamp()),
				'auto_sigfield': False,
				'sigandcertify': certify,
				'signaturebox': (0, 0, 0, 0),
				'contact': '',
				'location': '',
				'reason': '',
				'signingdate': strDate,
			}

			if(self.chkDrawStamp.isChecked()):
				dlg = SimpleSignerPreviewWindow(self, pdfPath)
				dlg.exec_()
				if(dlg.stampRect == None or dlg.stampPage == None): return
				dct['signaturebox'] = dlg.stampRect
				dct['sigpage'] = dlg.stampPage
				dct['signature_appearance'] = {
					'background': [0.75, 0.8, 0.95],
					'outline': [0.2, 0.3, 0.5],
					'border': 1,
					'labels': True,
					'display': ['CN', 'date'],
				}
				if(os.path.exists(self.txtStampPath.text())):
					dct['signature_appearance']['icon'] = self.txtStampPath.text()

			else:
				dct['signature'] = ''

			self.DoSign(pdfPath, signedPdfPath, dct)

		except Exception as e:
			# error message
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setWindowTitle('😕')
			msg.setText(str(e))
			msg.setStandardButtons(QMessageBox.Ok)
			retval = msg.exec_()

	def DoSign(self, pdfPath, signedPdfPath, dct):
		try:
			# load certificate
			certData = open(self.txtCertPath.text(), 'rb').read()
			p12Data = pkcs12.load_key_and_certificates(certData, str.encode(self.txtCertPassword.text()), backends.default_backend())

			# check certificate
			if(p12Data[1] != None and p12Data[1].not_valid_after < datetime.datetime.now()):
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setWindowTitle(QApplication.translate('SimpleSigner', 'Certificate Warning'))
				msg.setText(QApplication.translate('SimpleSigner', 'Your certificate expired on %s. Continue?') % str(p12Data[1].not_valid_after))
				msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
				if(msg.exec_() == QMessageBox.Cancel): return

			# load source PDF
			pdfData = open(pdfPath, 'rb').read()

			# sign
			signData = cms.sign(pdfData, dct, p12Data[0], p12Data[1], p12Data[2], 'sha256')

			# save signed target PDF
			with open(signedPdfPath, 'wb') as fp:
				fp.write(pdfData)
				fp.write(signData)

				# success message
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Information)
				msg.setWindowTitle('😇')
				msg.setText(QApplication.translate('SimpleSigner', 'Successfully saved as »%s«.') % signedPdfPath)
				msg.setStandardButtons(QMessageBox.Ok)
				btnOpen = msg.addButton(QApplication.translate('SimpleSigner', 'Open Directory'), QMessageBox.ActionRole)
				btnOpen.clicked.connect(self.OnClickOpenSignedInFileManager)
				btnOpen = msg.addButton(QApplication.translate('SimpleSigner', 'Open Signed PDF'), QMessageBox.ActionRole)
				btnOpen.clicked.connect(self.OnClickOpenSigned)
				retval = msg.exec_()

		except Exception as e:
			# error message
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setWindowTitle('😕')
			msg.setText(str(e))
			msg.setStandardButtons(QMessageBox.Ok)
			retval = msg.exec_()

	def getSignedPdfFileName(self):
		originalFileName = self.txtPdfPath.text()
		if originalFileName.lower().endswith('.pdf'):
			return originalFileName[:-4]+'-signed.pdf'
		else:
			return originalFileName+'-signed.pdf'

	def existsBinary(self, name):
		return which(name) is not None

def main():
	app = QApplication(sys.argv)
	translator = QTranslator(app)
	if(os.path.isdir('lang')):
		translator.load('lang/%s.qm' % getdefaultlocale()[0])
	else:
		translator.load('/usr/share/simple-signer/lang/%s.qm' % getdefaultlocale()[0])
	app.installTranslator(translator)

	window = SimpleSignerMainWindow()
	window.show()

	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
