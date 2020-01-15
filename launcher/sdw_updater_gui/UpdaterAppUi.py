# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sdw_updater.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:

    def _fromUtf8(s):
        return s


try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)


except AttributeError:

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class Ui_UpdaterDialog(object):
    def setupUi(self, UpdaterDialog):
        UpdaterDialog.setObjectName(_fromUtf8("UpdaterDialog"))
        UpdaterDialog.resize(520, 450)
        self.layoutWidget = QtGui.QWidget(UpdaterDialog)
        self.layoutWidget.setGeometry(QtCore.QRect(20, 20, 480, 410))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.layoutWidget.sizePolicy().hasHeightForWidth())
        self.layoutWidget.setSizePolicy(sizePolicy)
        self.layoutWidget.setMinimumSize(QtCore.QSize(480, 410))
        self.layoutWidget.setMaximumSize(QtCore.QSize(480, 410))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.proposedActionLabel = QtGui.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.proposedActionLabel.setFont(font)
        self.proposedActionLabel.setObjectName(_fromUtf8("proposedActionLabel"))
        self.gridLayout.addWidget(self.proposedActionLabel, 3, 0, 1, 3)
        self.progressBar = QtGui.QProgressBar(self.layoutWidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 3)
        self.clientOpenButton = QtGui.QPushButton(self.layoutWidget)
        self.clientOpenButton.setObjectName(_fromUtf8("clientOpenButton"))
        self.gridLayout.addWidget(self.clientOpenButton, 5, 1, 1, 1)
        self.rebootButton = QtGui.QPushButton(self.layoutWidget)
        self.rebootButton.setObjectName(_fromUtf8("rebootButton"))
        self.gridLayout.addWidget(self.rebootButton, 5, 2, 1, 1)
        self.applyUpdatesButton = QtGui.QPushButton(self.layoutWidget)
        self.applyUpdatesButton.setObjectName(_fromUtf8("applyUpdatesButton"))
        self.gridLayout.addWidget(self.applyUpdatesButton, 5, 0, 1, 1)
        self.proposedActionDescription = QtGui.QLabel(self.layoutWidget)
        self.proposedActionDescription.setWordWrap(True)
        self.proposedActionDescription.setObjectName(
            _fromUtf8("proposedActionDescription")
        )
        self.gridLayout.addWidget(self.proposedActionDescription, 4, 0, 1, 3)

        self.retranslateUi(UpdaterDialog)
        QtCore.QMetaObject.connectSlotsByName(UpdaterDialog)

    def retranslateUi(self, UpdaterDialog):
        UpdaterDialog.setWindowTitle(
            _translate(
                "UpdaterDialog", "SecureDrop Workstation preflight updater", None
            )
        )
        self.proposedActionLabel.setText(
            _translate("UpdaterDialog", "User Notifications go here", None)
        )
        self.clientOpenButton.setText(_translate("UpdaterDialog", "Open Client", None))
        self.rebootButton.setText(_translate("UpdaterDialog", "Reboot", None))
        self.applyUpdatesButton.setText(
            _translate("UpdaterDialog", "Start Updates", None)
        )
        self.proposedActionDescription.setText(
            _translate("UpdaterDialog", "Description goes here", None)
        )
