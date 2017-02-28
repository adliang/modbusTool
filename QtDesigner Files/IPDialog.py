# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'IPDialog.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_IPDialog(object):
    def setupUi(self, IPDialog):
        IPDialog.setObjectName("IPDialog")
        IPDialog.resize(332, 144)
        IPDialog.setMinimumSize(QtCore.QSize(300, 110))
        IPDialog.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.gridLayout = QtWidgets.QGridLayout(IPDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(IPDialog)
        self.lineEdit.setMaximumSize(QtCore.QSize(50, 16777215))
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.label_2 = QtWidgets.QLabel(IPDialog)
        self.label_2.setMaximumSize(QtCore.QSize(10, 10))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(IPDialog)
        self.lineEdit_2.setMaximumSize(QtCore.QSize(50, 16777215))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout.addWidget(self.lineEdit_2)
        self.label_3 = QtWidgets.QLabel(IPDialog)
        self.label_3.setMaximumSize(QtCore.QSize(10, 10))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.lineEdit_3 = QtWidgets.QLineEdit(IPDialog)
        self.lineEdit_3.setMaximumSize(QtCore.QSize(50, 16777215))
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.horizontalLayout.addWidget(self.lineEdit_3)
        self.label_4 = QtWidgets.QLabel(IPDialog)
        self.label_4.setMaximumSize(QtCore.QSize(10, 10))
        self.label_4.setScaledContents(True)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.lineEdit_4 = QtWidgets.QLineEdit(IPDialog)
        self.lineEdit_4.setMaximumSize(QtCore.QSize(50, 16777215))
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.horizontalLayout.addWidget(self.lineEdit_4)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 2)
        self.buttonBox = QtWidgets.QDialogButtonBox(IPDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.label = QtWidgets.QLabel(IPDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem, 2, 1, 1, 1)

        self.retranslateUi(IPDialog)
        self.buttonBox.accepted.connect(IPDialog.accept)
        self.buttonBox.rejected.connect(IPDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(IPDialog)

    def retranslateUi(self, IPDialog):
        _translate = QtCore.QCoreApplication.translate
        IPDialog.setWindowTitle(_translate("IPDialog", "IP Setup"))
        self.label_2.setText(_translate("IPDialog", "."))
        self.label_3.setText(_translate("IPDialog", "."))
        self.label_4.setText(_translate("IPDialog", "."))
        self.label.setText(_translate("IPDialog", "Enter IP Address:"))

