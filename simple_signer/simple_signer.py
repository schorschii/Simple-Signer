#!/usr/bin/env python3
# *-* coding: utf-8 *-*

from .__init__ import __title__, __version__, __website__

import sys, os, io
import datetime
import subprocess
import configparser
import json
import traceback
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
		labelAppName.setText(self.parentWidget().PRODUCT_NAME + ' v' + self.parentWidget().PRODUCT_VERSION)
		labelAppName.setStyleSheet('font-weight:bold')
		labelAppName.setAlignment(Qt.AlignCenter)
		self.layout.addWidget(labelAppName)

		labelCopyright = QLabel(self)
		labelCopyright.setText(
			'<br>'
			'© 2021-2022 <a href=\'https://georg-sieber.de\'>Georg Sieber</a>'
			'<br>'
			'<br>'
			'GNU General Public License v3.0'
			'<br>'
			'<a href=\''+self.parentWidget().PRODUCT_WEBSITE+'\'>'+self.parentWidget().PRODUCT_WEBSITE+'</a>'
			'<br>'
		)
		labelCopyright.setOpenExternalLinks(True)
		labelCopyright.setAlignment(Qt.AlignCenter)
		self.layout.addWidget(labelCopyright)

		labelDescription = QLabel(self)
		labelDescription.setText(
			QApplication.translate('SimpleSigner', 'Simple-Signer allows you to to sign PDFs using a simple user interface.')
			+'\n\n'+
			QApplication.translate('SimpleSigner', 'Signing allows multiple users to place their digital signature on a document.')
			+'\n'+
			QApplication.translate('SimpleSigner', 'Certifiy will place your signature on the document and lock it after that.')
			+'\n'
		)
		labelDescription.setStyleSheet('opacity:0.8')
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
	pdfDocument = None

	stampRect = None
	stampPage = None

	def __init__(self, parent, pdfFilePath):
		super(SimpleSignerPreviewWindow, self).__init__(parent)
		self.pdfFilePath = pdfFilePath

		# load PDF document
		import fitz
		from PIL.ImageQt import ImageQt
		self.pdfDocument = fitz.open(self.pdfFilePath)
		if(self.pdfDocument.page_count == 0):
			raise Exception(QApplication.translate('SimpleSigner', 'PDF is empty!'))

		self.InitUI()

	def InitUI(self):
		# Window Content
		grid = QGridLayout()

		lblInstructions = QLabel(QApplication.translate('SimpleSigner', 'Please select the rectangular area where you stamp should be placed by clicking and holding the left mouse button.'))
		lblInstructions.setWordWrap(True)
		grid.addWidget(lblInstructions, 0, 0)

		grid2 = QGridLayout()
		label = QLabel(QApplication.translate('SimpleSigner', 'Page:'))
		grid2.addWidget(label, 0, 0)
		self.sltPage = QComboBox()
		for i in range(0, self.pdfDocument.page_count):
			self.sltPage.addItem(str(i + 1))
		self.sltPage.currentIndexChanged.connect(self.OnCurrentIndexChanged)
		grid2.addWidget(self.sltPage, 0, 1)
		grid.addLayout(grid2, 1, 0)

		self.lblPageView = SimpleSignerPreview()
		self.lblPageView.setScaledContents(True)
		self.lblPageView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.lblPageView.setPixmap(self.pymupixmap2qpixmap(self.pdfDocument[0].get_pixmap()))
		grid.addWidget(self.lblPageView, 2, 0)

		self.btnDone = QPushButton(QApplication.translate('SimpleSigner', 'Done'))
		boldFont = QFont()
		boldFont.setBold(True)
		self.btnDone.setFont(boldFont)
		self.btnDone.clicked.connect(self.OnClickDone)
		grid.addWidget(self.btnDone, 3, 0)

		self.setLayout(grid)

		# Window Settings
		self.setMinimumSize(400, 600)
		self.setWindowTitle(QApplication.translate('SimpleSigner', 'Place Stamp'))

	# function to convert PyMuPDF pixmap object to QT pixmap for usage in QT controls
	def pymupixmap2qpixmap(self, image):
		bytes_img = io.BytesIO()
		image.pil_save(bytes_img, format='JPEG')
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
		# load page preview
		self.lblPageView.setPixmap(self.pymupixmap2qpixmap(self.pdfDocument[index].get_pixmap()))

	def OnClickDone(self, e):
		if(self.lblPageView.rect == None):
			self.close()
			return

		pageDimensions = self.pdfDocument[self.sltPage.currentIndex()].mediabox_size
		normalizedRect = self.lblPageView.rect.normalized()
		rect = [ normalizedRect.x(), normalizedRect.y(), normalizedRect.width(), normalizedRect.height() ]
		rect = self.translateRectCoordinateOrigin(rect, self.lblPageView.height())
		rect = self.translateRectToRealSize(rect, self.lblPageView.width(), self.lblPageView.height(), pageDimensions.x, pageDimensions.y)

		self.stampPage = self.sltPage.currentIndex()
		self.stampRect = rect
		self.close()

class SimpleSignerMainWindow(QMainWindow):
	PRODUCT_NAME      = __title__
	PRODUCT_VERSION   = __version__
	PRODUCT_WEBSITE   = __website__
	CONFIG_PATH       = str(Path.home())+'/.config/Simple-Signer/settings.ini'
	CONFIG_PATH_OLD   = str(Path.home())+'/.simple-signer.ini'

	config            = None
	signedPdfPath     = None

	signatureContact  = ''
	signatureLocation = ''
	signatureReason   = ''
	stampBackground   = [0.75, 0.80, 0.95]
	stampOutline      = [0.20, 0.30, 0.50]
	stampBorder       = 1
	stampLabels       = ['CN', 'date']

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
		self.txtStampPath.setPlaceholderText(QApplication.translate('SimpleSigner', '(Optional Stamp Image or Configuration File)'))
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
		if(not os.path.isdir(os.path.dirname(self.CONFIG_PATH))):
			os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
		if(os.path.exists(self.CONFIG_PATH_OLD)):
			os.rename(self.CONFIG_PATH_OLD, self.CONFIG_PATH)
		self.config = configparser.ConfigParser()
		if os.path.exists(self.CONFIG_PATH):
			self.config.read(self.CONFIG_PATH)
			if(not self.config.has_section('settings')): self.config.add_section('settings')
			self.txtCertPath.setText(self.config['settings'].get('cert-path', ''))
			self.txtStampPath.setText(self.config['settings'].get('stamp-path', ''))
			self.chkDrawStamp.setChecked(True if self.config['settings'].get('draw-stamp','0')=='1' else False)
			self.signatureContact  = self.config['settings'].get('signature-contact', self.signatureContact)
			self.signatureLocation = self.config['settings'].get('signature-location', self.signatureLocation)
			self.signatureReason   = self.config['settings'].get('signature-reason', self.signatureReason)
			if('stamp-background' in self.config['settings']):
				self.stampBackground = self.strArrayToFloatArray(self.config['settings']['stamp-background'].split(','))
			if('stamp-outline' in self.config['settings']):
				self.stampOutline = self.strArrayToFloatArray(self.config['settings']['stamp-outline'].split(','))
			if('stamp-border' in self.config['settings']):
				self.stampBorder = int(self.config['settings']['stamp-border'])
			if('stamp-labels' in self.config['settings']):
				self.stampLabels = self.config['settings']['stamp-labels'].split(',')

		# Defaults From Command Line
		if len(sys.argv) > 1: self.txtPdfPath.setText(sys.argv[1])
		if len(sys.argv) > 2: self.txtCertPath.setText(sys.argv[2])

	def closeEvent(self, event):
		# Write Settings To File
		if(not self.config.has_section('settings')): self.config.add_section('settings')
		self.config['settings']['cert-path'] = self.txtCertPath.text()
		self.config['settings']['stamp-path'] = self.txtStampPath.text()
		self.config['settings']['draw-stamp'] = '1' if self.chkDrawStamp.isChecked() else '0'
		with open(self.CONFIG_PATH, 'w') as configfile:
			self.config.write(configfile)
		event.accept()

	def strArrayToFloatArray(self, strArray):
		floatArray = []
		for item in strArray:
			floatArray.append(float(item))
		return floatArray

	def OnOpenAboutDialog(self, e):
		dlg = SimpleSignerAboutWindow(self)
		dlg.exec_()

	def OnClickChoosePdfPath(self, e):
		fileName = self.OpenFileDialog(QApplication.translate('SimpleSigner', 'PDF File'), 'PDF Files (*.pdf);;All Files (*.*)')
		if fileName: self.txtPdfPath.setText(fileName)

	def OnClickChooseCertPath(self, e):
		fileName = self.OpenFileDialog(QApplication.translate('SimpleSigner', 'Certificate File'), 'Certificate Files (*.p12 *.pfx);;All Files (*.*)')
		if fileName: self.txtCertPath.setText(fileName)

	def OnClickChooseStampPath(self, e):
		fileName = self.OpenFileDialog(QApplication.translate('SimpleSigner', 'Stamp Image File'), 'Image Files (*.jpg *.png);;Stamp Manifest Files (*.stampinfo);;All Files (*.*)')
		if fileName: self.txtStampPath.setText(fileName)

	def OpenFileDialog(self, title, filter):
		fileName, _ = QFileDialog.getOpenFileName(self, title, None, filter)
		return fileName

	def SaveFileDialog(self, title, default, filter):
		fileName, _ = QFileDialog.getSaveFileName(self, title, default, filter)
		return fileName

	def OnClickOpenSigned(self, e):
		if sys.platform == 'win32': # Windows
			subprocess.Popen([self.signedPdfPath], shell=True)
			return
		if self.existsBinary('okular'): # Okular displays signatures
			cmd = ['okular', self.signedPdfPath]
		elif self.existsBinary('libreoffice'): # LibreOffice displays signatures
			cmd = ['libreoffice', self.signedPdfPath]
		elif self.existsBinary('xdg-open'): # Linux fallback
			cmd = ['xdg-open', self.signedPdfPath]
		elif self.existsBinary('open'): # macOS
			cmd = ['open', self.signedPdfPath]
		res = subprocess.Popen(cmd, start_new_session=True)

	def OnClickOpenSignedInFileManager(self, e):
		if sys.platform == 'win32': # Windows
			cmd = ['explorer', '/select,', os.path.normpath(self.signedPdfPath)]
		elif self.existsBinary('nemo'): # Linux Mint
			cmd = ['nemo', self.signedPdfPath]
		elif self.existsBinary('nautilus'): # Ubuntu
			cmd = ['nautilus', self.signedPdfPath]
		elif self.existsBinary('nautilus'): # Linux fallback
			cmd = ['xdg-open', os.path.dirname(self.signedPdfPath)]
		elif self.existsBinary('open'): # macOS
			cmd = ['open', os.path.dirname(self.signedPdfPath)]
		res = subprocess.Popen(cmd, start_new_session=True)

	def OnReturnPressed(self):
		self.OnClickSign(None)

	def OnClickSign(self, e):
		self.Sign(False)

	def OnClickCertify(self, e):
		self.Sign(True)

	def Sign(self, certify):
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

			# get source path
			pdfPath = self.txtPdfPath.text()

			# compile sign options
			dct = {
				'sigflags': 3,
				'sigflagsft': 132,
				'sigpage': 0,
				'sigbutton': False,
				'sigfield': 'Signature-'+str(datetime.datetime.utcnow().timestamp()),
				'auto_sigfield': False,
				'sigandcertify': certify,
				'signaturebox': (0, 0, 0, 0),
				'contact': self.signatureContact,
				'location': self.signatureLocation,
				'reason': self.signatureReason,
				'signingdate': datetime.datetime.utcnow().strftime("D:%Y%m%d%H%M%S+00'00'"),
			}

			if(self.chkDrawStamp.isChecked()):
				stampInfo = None
				if(self.txtStampPath.text().endswith('.stampinfo') and os.path.exists(self.txtStampPath.text())):
					with open(self.txtStampPath.text()) as f: stampInfo = json.load(f)

				if(stampInfo == None):
					# show dialog to draw stamp rect
					dlg = SimpleSignerPreviewWindow(self, pdfPath)
					dlg.exec_()
					if(dlg.stampRect == None or dlg.stampPage == None): return
					print('You can create a config file (*.stampinfo) with the following content to automate the signature process: ', json.dumps({
						'rect': dlg.stampRect,
						'page': dlg.stampPage
					}))
					dct['signaturebox'] = dlg.stampRect
					dct['sigpage'] = dlg.stampPage
					dct['signature_appearance'] = {
						'background': self.stampBackground,
						'outline': self.stampOutline,
						'border': self.stampBorder,
						'labels': True,
						'display': self.stampLabels,
					}
					# use stamp image if given
					if(os.path.exists(self.txtStampPath.text())):
						dct['signature_appearance']['icon'] = self.txtStampPath.text()
				else:
					# draw stamp automatically using stamp info
					print('Using .stampinfo: ', stampInfo)
					dct['signaturebox'] = stampInfo['rect']
					dct['sigpage'] = stampInfo['page'] if 'page' in stampInfo else '0'
					dct['signature_appearance'] = stampInfo['signature_appearance'] if 'signature_appearance' in stampInfo else {
						'background': self.stampBackground,
						'outline': self.stampOutline,
						'border': self.stampBorder,
						'labels': True,
						'display': self.stampLabels,
					}

			else:
				dct['signature'] = ''

			# get target path
			self.signedPdfPath = self.SaveFileDialog(QApplication.translate('SimpleSigner', 'Save Filename for Signed PDF'), self.getDefaultSignedPdfFileName(), 'PDF Files (*.pdf);;All Files (*.*)')
			if not self.signedPdfPath: return

			# do it
			self.DoSign(pdfPath, dct, p12Data)

		except Exception as e:
			# error message
			traceback.print_exc()
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setWindowTitle('😕')
			msg.setText(str(type(e))+': '+str(e))
			msg.setStandardButtons(QMessageBox.Ok)
			retval = msg.exec_()

	def DoSign(self, pdfPath, dct, p12Data):
		try:
			# load source PDF
			pdfData = open(pdfPath, 'rb').read()

			# sign
			signData = cms.sign(pdfData, dct, p12Data[0], p12Data[1], p12Data[2], 'sha256')

			# save signed target PDF
			with open(self.signedPdfPath, 'wb') as fp:
				fp.write(pdfData)
				fp.write(signData)

				# success message
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Information)
				msg.setWindowTitle('😇')
				msg.setText(QApplication.translate('SimpleSigner', 'Successfully saved as »%s«.') % self.signedPdfPath)
				msg.setStandardButtons(QMessageBox.Ok)
				btnOpen = msg.addButton(QApplication.translate('SimpleSigner', 'Open Directory'), QMessageBox.ActionRole)
				btnOpen.clicked.connect(self.OnClickOpenSignedInFileManager)
				btnOpen = msg.addButton(QApplication.translate('SimpleSigner', 'Open Signed PDF'), QMessageBox.ActionRole)
				btnOpen.clicked.connect(self.OnClickOpenSigned)
				retval = msg.exec_()

		except Exception as e:
			# error message
			traceback.print_exc()
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setWindowTitle('😕')
			msg.setText(str(type(e))+': '+str(e))
			msg.setStandardButtons(QMessageBox.Ok)
			retval = msg.exec_()

	def getDefaultSignedPdfFileName(self):
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
	if getattr(sys, 'frozen', False):
		translator.load(os.path.join(sys._MEIPASS, 'lang/%s.qm' % getdefaultlocale()[0]))
	elif os.path.isdir('lang'):
		translator.load('lang/%s.qm' % getdefaultlocale()[0])
	else:
		translator.load('/usr/share/simple-signer/lang/%s.qm' % getdefaultlocale()[0])
	app.installTranslator(translator)

	window = SimpleSignerMainWindow()
	window.show()

	sys.exit(app.exec_())
