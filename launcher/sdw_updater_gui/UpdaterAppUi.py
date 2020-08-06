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
        UpdaterDialog.resize(520, 300)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(UpdaterDialog.sizePolicy().hasHeightForWidth())
        UpdaterDialog.setSizePolicy(sizePolicy)
        UpdaterDialog.setMaximumSize(QtCore.QSize(600, 420))
        self.gridLayout_2 = QtGui.QGridLayout(UpdaterDialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setContentsMargins(-1, 15, -1, 15)
        self.gridLayout.setHorizontalSpacing(3)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem, 1, 1, 1, 5)
        self.clientOpenButton = QtGui.QPushButton(UpdaterDialog)
        self.clientOpenButton.setStyleSheet(_fromUtf8(""))
        self.clientOpenButton.setAutoDefault(True)
        self.clientOpenButton.setObjectName(_fromUtf8("clientOpenButton"))
        self.gridLayout.addWidget(self.clientOpenButton, 7, 4, 1, 1)
        self.proposedActionDescription = QtGui.QLabel(UpdaterDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.proposedActionDescription.sizePolicy().hasHeightForWidth()
        )
        self.proposedActionDescription.setSizePolicy(sizePolicy)
        self.proposedActionDescription.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
        )
        self.proposedActionDescription.setWordWrap(True)
        self.proposedActionDescription.setObjectName(_fromUtf8("proposedActionDescription"))
        self.gridLayout.addWidget(self.proposedActionDescription, 4, 1, 1, 5)
        spacerItem1 = QtGui.QSpacerItem(
            40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum
        )
        self.gridLayout.addItem(spacerItem1, 7, 1, 1, 1)
        self.rebootButton = QtGui.QPushButton(UpdaterDialog)
        self.rebootButton.setStyleSheet(_fromUtf8(""))
        self.rebootButton.setAutoDefault(True)
        self.rebootButton.setObjectName(_fromUtf8("rebootButton"))
        self.gridLayout.addWidget(self.rebootButton, 7, 3, 1, 1)
        self.applyUpdatesButton = QtGui.QPushButton(UpdaterDialog)
        self.applyUpdatesButton.setStyleSheet(_fromUtf8(""))
        self.applyUpdatesButton.setAutoDefault(True)
        self.applyUpdatesButton.setDefault(False)
        self.applyUpdatesButton.setObjectName(_fromUtf8("applyUpdatesButton"))
        self.gridLayout.addWidget(self.applyUpdatesButton, 7, 2, 1, 1)
        self.cancelButton = QtGui.QPushButton(UpdaterDialog)
        self.cancelButton.setStyleSheet(_fromUtf8(""))
        self.cancelButton.setAutoDefault(True)
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.gridLayout.addWidget(self.cancelButton, 7, 5, 1, 1)
        self.progressBar = QtGui.QProgressBar(UpdaterDialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 2, 1, 1, 5)
        self.headline = QtGui.QLabel(UpdaterDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.headline.sizePolicy().hasHeightForWidth())
        self.headline.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        self.headline.setFont(font)
        self.headline.setObjectName(_fromUtf8("headline"))
        self.gridLayout.addWidget(self.headline, 0, 1, 1, 5)
        spacerItem2 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem2, 3, 1, 1, 5)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(UpdaterDialog)
        QtCore.QMetaObject.connectSlotsByName(UpdaterDialog)

    def retranslateUi(self, UpdaterDialog):
        UpdaterDialog.setWindowTitle(
            _translate("UpdaterDialog", "SecureDrop Workstation preflight updater", None)
        )
        self.clientOpenButton.setText(_translate("UpdaterDialog", "Continue", None))
        self.proposedActionDescription.setText(
            _translate("UpdaterDialog", "Description goes here", None)
        )
        self.rebootButton.setText(_translate("UpdaterDialog", "Reboot", None))
        self.applyUpdatesButton.setText(_translate("UpdaterDialog", "Start Updates", None))
        self.cancelButton.setText(_translate("UpdaterDialog", "Cancel", None))
        self.headline.setText(_translate("UpdaterDialog", "Headline goes here", None))
