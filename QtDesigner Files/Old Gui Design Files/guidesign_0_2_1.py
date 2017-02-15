# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'guidesign_0_2_1.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QFrame
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 698)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../modbus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setMaximumSize(QtCore.QSize(350, 16777215))
        self.treeWidget.setRootIsDecorated(True)
        self.treeWidget.setUniformRowHeights(False)
        self.treeWidget.setItemsExpandable(True)
        self.treeWidget.setAnimated(True)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.treeWidget.header().setVisible(False)
        self.verticalLayout_2.addWidget(self.treeWidget)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnWrite = QtWidgets.QPushButton(self.centralwidget)
        self.btnWrite.setObjectName("btnWrite")
        self.horizontalLayout_2.addWidget(self.btnWrite)
        self.btnUnits = QtWidgets.QPushButton(self.centralwidget)
        self.btnUnits.setObjectName("btnUnits")
        self.horizontalLayout_2.addWidget(self.btnUnits)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.comboBoxDataEncode = QtWidgets.QComboBox(self.centralwidget)
        self.comboBoxDataEncode.setObjectName("comboBoxDataEncode")
        self.comboBoxDataEncode.addItem("")
        self.comboBoxDataEncode.addItem("")
        self.horizontalLayout_2.addWidget(self.comboBoxDataEncode)
        self.checkBoxPoll = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxPoll.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.checkBoxPoll.setObjectName("checkBoxPoll")
        self.horizontalLayout_2.addWidget(self.checkBoxPoll)
        self.checkDebug = QtWidgets.QCheckBox(self.centralwidget)
        self.checkDebug.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.checkDebug.setObjectName("checkDebug")
        self.horizontalLayout_2.addWidget(self.checkDebug)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setToolTip("")
        self.label.setAutoFillBackground(False)
        self.label.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label.setScaledContents(False)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setWordWrap(False)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.spinBoxPollRate = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.spinBoxPollRate.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.spinBoxPollRate.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.spinBoxPollRate.setProperty("showGroupSeparator", False)
        self.spinBoxPollRate.setDecimals(3)
        self.spinBoxPollRate.setMinimum(0.01)
        self.spinBoxPollRate.setSingleStep(0.1)
        self.spinBoxPollRate.setProperty("value", 0.3)
        self.spinBoxPollRate.setObjectName("spinBoxPollRate")
        self.horizontalLayout_2.addWidget(self.spinBoxPollRate)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.btnStar = QtWidgets.QPushButton(self.centralwidget)
        self.btnStar.setObjectName("btnStar")
        self.gridLayout.addWidget(self.btnStar, 0, 0, 1, 1)
        self.btnReset = QtWidgets.QPushButton(self.centralwidget)
        self.btnReset.setObjectName("btnReset")
        self.gridLayout.addWidget(self.btnReset, 0, 1, 1, 1)
        self.btnTest = QtWidgets.QPushButton(self.centralwidget)
        self.btnTest.setObjectName("btnTest")
        self.gridLayout.addWidget(self.btnTest, 0, 2, 1, 1)
        self.btnSto = QtWidgets.QPushButton(self.centralwidget)
        self.btnSto.setObjectName("btnSto")
        self.gridLayout.addWidget(self.btnSto, 1, 0, 1, 1)
        self.btnLoadDefaults = QtWidgets.QPushButton(self.centralwidget)
        self.btnLoadDefaults.setObjectName("btnLoadDefaults")
        self.gridLayout.addWidget(self.btnLoadDefaults, 1, 1, 1, 1)
        self.btnUpdate = QtWidgets.QPushButton(self.centralwidget)
        self.btnUpdate.setObjectName("btnUpdate")
        self.gridLayout.addWidget(self.btnUpdate, 1, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setToolTip("")
        self.tableWidget.setToolTipDuration(-1)
        self.tableWidget.setGridStyle(QtCore.Qt.SolidLine)
        self.tableWidget.setCornerButtonEnabled(False)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, item)

        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setSortIndicatorShown(False)
        self.tableWidget.horizontalHeader().setStretchLastSection(False)
        self.tableWidget.verticalHeader().setVisible(True)
        self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
        self.tableWidget.verticalHeader().setSortIndicatorShown(False)
        self.tableWidget.verticalHeader().setStretchLastSection(False)
        self.verticalLayout.addWidget(self.tableWidget)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        self.m_statusleft = QLabel("")
        self.m_statusleft.setFrameStyle(QFrame.Sunken)
        self.m_statusmid = QLabel("IP:")
        self.m_statusmid.setFrameStyle(QFrame.Sunken)
        self.m_statusright = QLabel("TX:")
        self.m_statusright.setFrameStyle(QFrame.Panel)
        self.statusBar.addPermanentWidget(self.m_statusleft, 1)
        self.statusBar.addPermanentWidget(self.m_statusmid, 2)
        self.statusBar.addPermanentWidget(self.m_statusright, 3)
        MainWindow.setStatusBar(self.statusBar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1250, 21))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QtWidgets.QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QtWidgets.QMenu(self.menuBar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menuBar)
        self.actionSetup = QtWidgets.QAction(MainWindow)
        self.actionSetup.setObjectName("actionSetup")
        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionSave_View_List = QtWidgets.QAction(MainWindow)
        self.actionSave_View_List.setObjectName("actionSave_View_List")
        self.actionLoad_View_List = QtWidgets.QAction(MainWindow)
        self.actionLoad_View_List.setObjectName("actionLoad_View_List")
        self.menuFile.addAction(self.actionSetup)
        self.menuFile.addAction(self.actionSave_View_List)
        self.menuFile.addAction(self.actionLoad_View_List)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Modbus Master Tool"))
        self.btnWrite.setText(_translate("MainWindow", "Write To Register"))
        self.btnUnits.setText(_translate("MainWindow", "Save Units"))
        self.label_2.setText(_translate("MainWindow", "Word Order"))
        self.comboBoxDataEncode.setItemText(0, _translate("MainWindow", "AB CD"))
        self.comboBoxDataEncode.setItemText(1, _translate("MainWindow", "CD AB"))
        self.checkBoxPoll.setText(_translate("MainWindow", "Poll"))
        self.checkDebug.setText(_translate("MainWindow", "Debug"))
        self.label.setText(_translate("MainWindow", "Poll Period"))
        self.btnStar.setText(_translate("MainWindow", "Start"))
        self.btnReset.setText(_translate("MainWindow", "Reset"))
        self.btnTest.setText(_translate("MainWindow", "Test"))
        self.btnSto.setText(_translate("MainWindow", "Stop"))
        self.btnLoadDefaults.setText(_translate("MainWindow", "Load Defaults"))
        self.btnUpdate.setText(_translate("MainWindow", "Update"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Value"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Units"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Write"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "Notes"))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "Diplay"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionSetup.setText(_translate("MainWindow", "Setup"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        self.actionSave_View_List.setText(_translate("MainWindow", "Save View List"))
        self.actionLoad_View_List.setText(_translate("MainWindow", "Load View List"))

