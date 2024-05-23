# Form implementation generated from reading ui file 'sdw_updater.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_UpdaterDialog:
    def setupUi(self, UpdaterDialog):
        UpdaterDialog.setObjectName("UpdaterDialog")
        UpdaterDialog.resize(520, 300)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(UpdaterDialog.sizePolicy().hasHeightForWidth())
        UpdaterDialog.setSizePolicy(sizePolicy)
        UpdaterDialog.setMaximumSize(QtCore.QSize(600, 420))
        self.gridLayout_2 = QtWidgets.QGridLayout(UpdaterDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setContentsMargins(-1, 15, -1, 15)
        self.gridLayout.setHorizontalSpacing(3)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(
            20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed
        )
        self.gridLayout.addItem(spacerItem, 1, 1, 1, 5)
        self.clientOpenButton = QtWidgets.QPushButton(UpdaterDialog)
        self.clientOpenButton.setStyleSheet("")
        self.clientOpenButton.setAutoDefault(True)
        self.clientOpenButton.setObjectName("clientOpenButton")
        self.gridLayout.addWidget(self.clientOpenButton, 7, 4, 1, 1)
        self.proposedActionDescription = QtWidgets.QLabel(UpdaterDialog)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )
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
        self.proposedActionDescription.setObjectName("proposedActionDescription")
        self.gridLayout.addWidget(self.proposedActionDescription, 4, 1, 1, 5)
        spacerItem1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.gridLayout.addItem(spacerItem1, 7, 1, 1, 1)
        self.rebootButton = QtWidgets.QPushButton(UpdaterDialog)
        self.rebootButton.setStyleSheet("")
        self.rebootButton.setAutoDefault(True)
        self.rebootButton.setObjectName("rebootButton")
        self.gridLayout.addWidget(self.rebootButton, 7, 3, 1, 1)
        self.applyUpdatesButton = QtWidgets.QPushButton(UpdaterDialog)
        self.applyUpdatesButton.setStyleSheet("")
        self.applyUpdatesButton.setAutoDefault(True)
        self.applyUpdatesButton.setDefault(False)
        self.applyUpdatesButton.setObjectName("applyUpdatesButton")
        self.gridLayout.addWidget(self.applyUpdatesButton, 7, 2, 1, 1)
        self.cancelButton = QtWidgets.QPushButton(UpdaterDialog)
        self.cancelButton.setStyleSheet("")
        self.cancelButton.setAutoDefault(True)
        self.cancelButton.setObjectName("cancelButton")
        self.gridLayout.addWidget(self.cancelButton, 7, 5, 1, 1)
        self.progressBar = QtWidgets.QProgressBar(UpdaterDialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.gridLayout.addWidget(self.progressBar, 2, 1, 1, 5)
        self.headline = QtWidgets.QLabel(UpdaterDialog)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
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
        self.headline.setObjectName("headline")
        self.gridLayout.addWidget(self.headline, 0, 1, 1, 5)
        spacerItem2 = QtWidgets.QSpacerItem(
            20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed
        )
        self.gridLayout.addItem(spacerItem2, 3, 1, 1, 5)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(UpdaterDialog)
        QtCore.QMetaObject.connectSlotsByName(UpdaterDialog)

    def retranslateUi(self, UpdaterDialog):
        _translate = QtCore.QCoreApplication.translate
        UpdaterDialog.setWindowTitle(
            _translate("UpdaterDialog", "SecureDrop Workstation preflight updater")
        )
        self.clientOpenButton.setText(_translate("UpdaterDialog", "Continue"))
        self.proposedActionDescription.setText(_translate("UpdaterDialog", "Description goes here"))
        self.rebootButton.setText(_translate("UpdaterDialog", "Reboot"))
        self.applyUpdatesButton.setText(_translate("UpdaterDialog", "Start Updates"))
        self.cancelButton.setText(_translate("UpdaterDialog", "Cancel"))
        self.headline.setText(_translate("UpdaterDialog", "Headline goes here"))
