#!/usr/bin/env python

"""Modbus Master Tool
"""

__version__ = '0.1.0'
__author__ = 'Andrew Liang'

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem
import guidesign
import sys
import os
from time import sleep
import threading
from tkinter import *
import tkinter.messagebox
import time
import random
import _thread
import win_inet_pton
import socket
from pyModbusTCP.client import ModbusClient
import json
from pprint import pprint
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import (QTreeWidgetItem, QTreeWidget, QTreeView, QTableWidget, QTableWidgetItem, QSpinBox,
                             QStatusBar, QDialog, QWidget, QPushButton, QLineEdit,
                             QInputDialog, QApplication, QInputDialog, QLabel, QFrame)
import logging
import struct
import copy
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget, QLineEdit
from PyQt5.QtCore import QSize, QRegExp
from PyQt5.QtGui import QRegExpValidator
x = 1
servers = ["127.0.0.1", "192.168.1.74"]

SERVER_HOST = servers[x]
SERVER_PORT = 502

# set global
global regpoll
pollList = []
regs = []


class SensorThread(QThread):
    regpoll = pyqtSignal(list)
    poll_rate = 1
    pollEn = False
    c = 0
    pollCountSignal = pyqtSignal(int)
    pollCount = 0

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def initIPaddress(self, ip):
        SensorThread.c = ModbusClient(host=ip, port=SERVER_PORT, auto_open=True, auto_close=True)

    def debugToggle(self, state):
        SensorThread.c.debug(state)

    def setPollRate(self, pollRate):
        SensorThread.poll_rate = pollRate

    def readSettings(self, addr, length):
        return SensorThread.c.read_holding_registers(addr, length)

    def writeSettings(self, addr, data):
        return SensorThread.c.write_multiple_registers(addr, data)

    def commandButton(self, command):
        return SensorThread.c.write_multiple_registers(1000, [command, 0])


    def writeToReg(self, writeArray, addrArray):
        for i in range(len(writeArray)):
            if writeArray[i]:
                try:
                    if SensorThread.c.write_multiple_registers(addrArray[i], writeArray[i]):

                        print('Write Success (%s %s)' % (addrArray[i],writeArray[i]))
                    else:
                        print("write Failure")
                except ValueError:
                    print('Write error')

    def run(self):
        global lenpollList
        while True:
            if  SensorThread.pollEn:
                if not SensorThread.c.is_open():
                    SensorThread.c.open()

                print("Last Except %s" %SensorThread.c.last_except())
                print("Last Error %s" %SensorThread.c.last_error())

                if pollList:
                    regs_list = [''] * lenpollList

                    for i in range(0, lenpollList):
                        try:
                            read_in = SensorThread.c.read_holding_registers(pollList[i]['address'], pollList[i]['length'])
                            SensorThread.pollCount += 1
                            self.pollCountSignal.emit(SensorThread.pollCount)
                            if read_in:
                                regs_list[i] = read_in

                        except IndexError:
                            print('Read error')
                            pass
                    regs = regs_list
                    #print('Register Values %s' % regs)
                    print("------------------------------------------------------")
                    self.regpoll.emit(regs)
                time.sleep(SensorThread.poll_rate)
            else:
                continue

class IPWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("IP Address")  # Set the window title
        central_widget = QWidget(self)  # Create a central widget
        self.setCentralWidget(central_widget)  # Install the central widget

        ipRange = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"  # Part of the regular expression
        # Regulare expression
        ipRegex = QRegExp("^" + ipRange + "\\." + ipRange + "\\." + ipRange + "\\." + ipRange + "$")
        ipValidator = QRegExpValidator(ipRegex, self)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setMaximumSize(QtCore.QSize(50, 16777215))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setValidator(ipValidator)

        self.horizontalLayout.addWidget(self.lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)


        grid_layout = QtWidgets.QGridLayout(self)  # Create QGridLayout
        central_widget.setLayout(grid_layout)  # Set this accommodation in central widget

        grid_layout.addWidget(QLabel("Enter IP Address: ", self), 0, 0)





class modbusTool(QtWidgets.QMainWindow, guidesign.Ui_MainWindow):
    # Table Columns
    colValue = 0
    colUnit = 1
    colWrite = 3
    colRemove = 4
    colMsg = 5
    colDisp = 2
    endianABCD = 0  # Big Endian Bytes, Reg 1 MSW
    endianCDAB = 1  # Big Endian Bytes, Reg 2 MSW

    endian = endianABCD  # Endian for floats
    last_child = 0

    decimal = 0
    hex = 1
    binary = 2
    writeDelay = 150 # ms

    def __init__(self, parent=None):
        super(modbusTool, self).__init__(parent)
        self.setupUi(self)
        SensorThread().initIPaddress(SERVER_HOST)  # Initialise modbus connection

        self.createTree()
        self.setPollRate()
        self.initViewList()
        self.updateTable()
        self.updateWriteButton()
        self.m_statusmid.setText("IP: %s" % SERVER_HOST)

        self.checkBoxPoll.stateChanged.connect(self.checkPollEn)
        self.checkDebug.stateChanged.connect(self.debugModeToggle)
        self.spinBoxPollRate.valueChanged.connect(self.setPollRate)
        self.comboBoxDataEncode.currentIndexChanged.connect(self.set_endian)
        self.comboBoxDataEncode.setCurrentIndex(1)

        self.get_thread = SensorThread()
        self.get_thread.start()
        self.get_thread.regpoll.connect(self.updateValues)
        self.get_thread.pollCountSignal.connect(self.updatePollCount)
        self.get_thread.finished.connect(self.done)

        self.btnUnits.clicked.connect(self.saveUnitsToFile)
        self.btnWrite.clicked.connect(self.writeToRegDelay)
        self.treeWidget.doubleClicked.connect(self.addTableEntry)
        self.tableWidget.cellDoubleClicked.connect(self.delTableEntry)

        self.btnUpdate.clicked.connect(self.commandUpdateBtnDelay)
        self.btnStop.clicked.connect(self.commandStopBtnDelay)
        self.btnStart.clicked.connect(self.commandStartBtnDelay)
        self.btnReset.clicked.connect(self.commandResetBtnDelay)
        self.btnLoadDefaults.clicked.connect(self.commandLoadDefaultsBtnDelay)
        self.btnTest.clicked.connect(self.commandTestBtnDelay)

        self.actionSetup.triggered.connect(self.initIP)

        self.actionSave_Settings.triggered.connect(self.saveSettings)
        self.actionSaveAs_Settings.triggered.connect(self.saveAsSettings)
        self.actionLoad_Settings.triggered.connect(self.loadSettings)

        self.actionSave_View_List.triggered.connect(self.saveViewList)
        self.actionSaveAs_View_List.triggered.connect(self.saveAsViewList)
        self.actionLoad_View_List.triggered.connect(self.loadViewList)

        self.actionQuit.triggered.connect(self.quitApp)

    # ---------------------------------------------------------------------------#
    # Initialises viewilist.ini view list
    # ---------------------------------------------------------------------------#
    def initViewList(self):
        global pollList
        global lenpollList
        try:
            with open('config//viewschema.json') as infile:
                viewListData = json.load(infile)
                infile.close()
                for i in viewListData['ViewList']:
                    pollList.append(mbmapVar[i])
                self.m_statusleft.setText("View schema loaded")
                lenpollList = len(pollList)
                self.updateTable()
        except:
            self.m_statusleft.setText("No view schema found...")

    # ---------------------------------------------------------------------------#
    # Menu Bar actions
    # ---------------------------------------------------------------------------#
    # Settings menu button
    def initIP(self):
        self.bob = IPWindow()
        self.bob.show()

    # Save view list menu button
    def saveViewList(self):
        toSaveViewList = []
        for i in pollList:
            toSaveViewList.append(i['varname'])
        text_file = open('config//viewschema.json', "w")
        json.dump({'ViewList': toSaveViewList}, text_file, indent=4, sort_keys=True)
        text_file.close()
        self.m_statusleft.setText("View schema saved!")

    def saveAsViewList(self):
        toSaveViewList = []

        def saveFileNameDialog():
            dialog = QFileDialog()

            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            # QFileDialog.setDefaultSuffix('*.json')
            fileName, _ = dialog.getSaveFileName(self, "Save As View Schema", "config",
                                                 "View Schema Files (*.json);; All Files (*)", options=options)
            if fileName:
                return fileName

        saveViewListFile = saveFileNameDialog()
        if saveViewListFile:
            for i in pollList:
                toSaveViewList.append(i['varname'])
            text_file = open(saveViewListFile + '.json', "w")
            json.dump({'ViewList': toSaveViewList}, text_file, indent=4, sort_keys=True)
            text_file.close()
            self.m_statusleft.setText("View schema saved!")
        else:
            return

    # Load view list menu button
    def loadViewList(self):
        SensorThread.pollEn = False
        global pollList
        global lenpollList

        def openFileNameDialog():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self, "Load View Schema", "config",
                                                      "View Schema Files (*.json);; All Files (*)", options=options)
            if fileName:
                return fileName

        userInfile = openFileNameDialog()

        if userInfile:
            try:
                with open(userInfile) as infile:
                    viewListData = json.load(infile)
                    infile.close()
                    pollList = []
                    for i in viewListData['ViewList']:
                        pollList.append(mbmapVar[i])
                    self.m_statusleft.setText("View schema loaded")
                    lenpollList = len(pollList)
                    self.updateTable()
            except:
                self.m_statusleft.setText("Invalid view schema file")
        else:
            self.checkPollEn()
            return

    # Quit menu button
    def quitApp(self):
        QtCore.QCoreApplication.instance().exit()

    # ---------------------------------------------------------------------------#
    # Save/Load Settings
    # ---------------------------------------------------------------------------#
    def saveSettings(self):
        self.m_statusleft.setText("Reading Settings. Please Wait...")
        SensorThread.pollEn = False

        saveSettingsList = {}
        temp_mbmap = copy.deepcopy(mbmap)

        for i in temp_mbmap:
            if 'Settings' in (i['varname']):
                settingReading = SensorThread().readSettings(i['address'], i['length'])
                i.update({'value' : settingReading})
                saveSettingsList.update({i['varname']: i})

        text_file = open('config//settings.json', "w")
        json.dump({'Settings':saveSettingsList}, text_file, indent=4, sort_keys=True)
        text_file.close()

        self.checkPollEn()
        self.m_statusleft.setText("Setting Saved!")

    def saveAsSettings(self):
        self.m_statusleft.setText("Reading Settings. Please Wait...")
        SensorThread.pollEn = False

        saveSettingsList = {}
        temp_mbmap = copy.deepcopy(mbmap)

        def saveFileNameDialog():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(self, "Save As Settings", "config",
                                                      "Settings Files (*.json);; All Files (*)", options=options)
            if fileName:
                return fileName

        saveSettingsFile = saveFileNameDialog()

        if saveSettingsFile:
            for i in temp_mbmap:
                if 'Settings' in (i['varname']):
                    settingReading = SensorThread().readSettings(i['address'], i['length'])
                    i.update({'value' : settingReading})
                    saveSettingsList.update({i['varname']: i})


            text_file = open(saveSettingsFile + '.json', "w")
            json.dump({'Settings':saveSettingsList}, text_file, indent=4, sort_keys=True)
            text_file.close()

            self.checkPollEn()
            self.m_statusleft.setText("Setting Saved!")
        else:
            return

    def loadSettings(self):
        SensorThread.pollEn = False

        def openFileNameDialog():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self, "Load Settings", "config",
                                                      "Settings Files (*.json);; All Files (*)", options=options)
            if fileName:
                return fileName

        userInfile = openFileNameDialog()

        if userInfile:
            try:
                with open(userInfile) as infile:
                    settings_data = json.load(infile)
                    infile.close()
                    settings_data = settings_data['Settings']

            except:
                self.m_statusleft.setText("Invalid Settings File")
                return

            for key in list(settings_data.keys()):
                if key in mbmapVar:
                    if settings_data[key]['type'] == mbmapVar[key]['type']:
                        if SensorThread().writeSettings(mbmapVar[key]['address'], settings_data[key]['value']):
                            continue
                        else:
                            print('ERROR WRITING  ', mbmapVar[key]['varname'], ' ', mbmapVar[key]['address'], ' ', settings_data[key]['value'])
            self.commandUpdateBtn()
            self.m_statusleft.setText("Setting Loaded!")
            self.checkPollEn()
        else:
            self.checkPollEn()
            return

    # ---------------------------------------------------------------------------#
    # Command buttons
    # ---------------------------------------------------------------------------#
    def commandStopBtnDelay(self):
        self.btnStop.setEnabled(False)
        SensorThread.pollEn = False
        QTimer.singleShot(modbusTool.writeDelay, self.commandStopBtn)
    def commandStopBtn(self):
        if SensorThread().commandButton(1):
            self.textBrowserCommand.setText("Stop Sent")
            print('Stop Command Sent')
        else:
            self.textBrowserCommand.setText("Stop Failed")
            print('Stop Command Not Sent')
        self.checkPollEn()
        self.btnStop.setEnabled(True)

    def commandResetBtnDelay(self):
        self.btnReset.setEnabled(False)
        SensorThread.pollEn = False
        QTimer.singleShot(modbusTool.writeDelay, self.commandResetBtn)
    def commandResetBtn(self):
        if SensorThread().commandButton(2):

            self.textBrowserCommand.setText("Reset Sent")
            print('Reset Command Sent')
        else:
            self.textBrowserCommand.setText("Reset Failed")
            print('Reset Command Not Sent')
        self.checkPollEn()
        self.btnReset.setEnabled(True)

    def commandStartBtnDelay(self):
        self.btnStart.setEnabled(False)
        SensorThread.pollEn = False
        QTimer.singleShot(modbusTool.writeDelay, self.commandStartBtn)
    def commandStartBtn(self):
        if SensorThread().commandButton(4):
            self.textBrowserCommand.setText("Start Sent")
            print('Start Command Sent')
        else:
            self.textBrowserCommand.setText("Start Failed")
            print('Start Command Not Sent')
        self.checkPollEn()
        self.btnStart.setEnabled(True)

    def commandTestBtnDelay(self):
        self.btnTest.setEnabled(False)
        SensorThread.pollEn = False
        QTimer.singleShot(modbusTool.writeDelay, self.commandTestBtn)
    def commandTestBtn(self):
        if SensorThread().commandButton(8):
            self.textBrowserCommand.setText("Test Sent")
            print('Test Command Sent')
        else:
            self.textBrowserCommand.setText("Test Failed")
            print('Test Command Not Sent')
        self.checkPollEn()
        self.btnTest.setEnabled(True)

    def commandLoadDefaultsBtnDelay(self):
        self.btnLoadDefaults.setEnabled(False)
        SensorThread.pollEn = False
        QTimer.singleShot(modbusTool.writeDelay, self.commandLoadDefaultsBtn)
    def commandLoadDefaultsBtn(self):
        if SensorThread().commandButton(16):
            self.textBrowserCommand.setText("Load Defaults Sent")
            print('Load Defaults Command Sent')
        else:
            self.textBrowserCommand.setText("Load Defaults Failed")
            print('Load Defaults Command Not Set')
        self.btnLoadDefaults.setEnabled(True)
        self.checkPollEn()

    def commandUpdateBtnDelay(self):
        self.btnUpdate.setEnabled(False)
        SensorThread.pollEn = False
        QTimer.singleShot(modbusTool.writeDelay, self.commandUpdateBtn)
    def commandUpdateBtn(self):
        if SensorThread().commandButton(32):
            self.textBrowserCommand.setText("Update Sent")
            print('Update Command Sent')
            for row in list(range(0, lenpollList)):
                if 'writepending' in pollList[row]:
                    pollList[row]['writepending'] = False
                    self.tableWidget.setItem(row, modbusTool.colWrite,  QTableWidgetItem(''))
        else:
            self.textBrowserCommand.setText("Update Failed")
            print('Update Command Not Set')
        self.checkPollEn()
        self.btnUpdate.setEnabled(True)

    # ---------------------------------------------------------------------------#
    # Generate tree widget from config.json
    # ---------------------------------------------------------------------------#
    def createTree(self):

        def fill_item(item, value):
            if type(value) is dict:
                for key, val in sorted(value.items()):
                    if key == 'Types':  # Do not parse the type size entry into tree
                        return

                    if key == 'mbrecord':
                        if 'ignore' in val:
                            if val['ignore']:
                                child = modbusTool.last_child
                                child.removeChild(child)
                                continue
                        else:
                            child = modbusTool.last_child
                            varname_tree = str(val["name"])
                            getParentNode = child.parent()
                            while getParentNode and getParentNode.text(0) != 'mbrecords':
                                varname_tree = getParentNode.text(0) + '.' + varname_tree
                                getParentNode = getParentNode.parent()
                            mbmapVar[val["varname"]].update({'treename' : varname_tree})
                            return

                    child = QTreeWidgetItem()
                    modbusTool.last_child = child
                    child.setText(0, str(key))
                    item.addChild(child)
                    fill_item(child, val)

        _translate = QtCore.QCoreApplication.translate
        self.treeWidget.clear()
        widget = QtWidgets.QTreeWidgetItem(self.treeWidget)
        widget.setText(0, _translate("MainWindow", 'Modbus Records'))
        fill_item(widget, config_file)
        self.treeWidget.expandToDepth(2)
        self.treeWidget.setExpandsOnDoubleClick(True)

    # ---------------------------------------------------------------------------#
    # Set poll rate to poll rate GUI element
    # ---------------------------------------------------------------------------#
    def setPollRate(self):
        SensorThread.poll_rate = self.spinBoxPollRate.value()

    # ---------------------------------------------------------------------------#
    # Set debug mode to debug checkbox GUI element
    # ---------------------------------------------------------------------------#
    def debugModeToggle(self):
        if self.checkDebug.checkState():
            SensorThread().debugToggle(True)
        else:
            SensorThread().debugToggle(False)

    # ---------------------------------------------------------------------------#
    # Set poll counter display to status bar GUI element
    # ---------------------------------------------------------------------------#
    def updatePollCount(self, pollCounter):
        self.m_statusright.setText("TX: %i" % pollCounter)

    # ---------------------------------------------------------------------------#
    # Set multiple word endian order to combo box GUI element
    # ---------------------------------------------------------------------------#
    def set_endian(self, endianVal):
        modbusTool.endian = endianVal

    # ---------------------------------------------------------------------------#
    # Start Stop polling from checkbox GUI element
    # ---------------------------------------------------------------------------#
    def checkPollEn(self):
        if self.checkBoxPoll.checkState():
            SensorThread.pollEn = True
            self.debugModeToggle()
        else:
            SensorThread.pollEn = False
            SensorThread().debugToggle(False)

    # ---------------------------------------------------------------------------#
    # Thread finished action
    # ---------------------------------------------------------------------------#
    def done(self):
        self.checkBoxPoll.setCheckState(0)

    # ---------------------------------------------------------------------------#
    # Save units button action
    # ---------------------------------------------------------------------------#
    def saveUnitsToFile(self):
        global lenpollList
        toSaveUnitsDict = {}
        for row in list(range(0, lenpollList)):
            unitsValue = self.tableWidget.item(row, modbusTool.colUnit)
            if unitsValue:
                try:
                    pollList[row].update({'units': unitsValue.text()})
                    configAddress = pollList[row]['treename']
                    configAddressSplit = configAddress.split('.')[1:]
                    configAddressSplit.reverse()
                    child = {"mbrecord": {"units": unitsValue.text()}}
                    for i in configAddressSplit:
                        temp_dict = {i: child}
                        child = temp_dict
                    toSaveUnitsDict = deepMerge(toSaveUnitsDict, temp_dict)
                except AttributeError:
                    print('Save Units Attr. Error')
                    continue
        try:
            with open('config\\units.json') as infile:
                units_file = json.load(infile)
                toSaveUnitsDict = deepMerge(units_file, toSaveUnitsDict)
                infile.close()
                text_file = open('config\\units.json', "w")
                json.dump(toSaveUnitsDict, text_file, indent=4, sort_keys=True)
                text_file.close()
        except FileNotFoundError:
            text_file = open('config\\units.json', "w")
            json.dump(toSaveUnitsDict, text_file, indent=4, sort_keys=True)
            text_file.close()
            print("units.json created")
        self.m_statusleft.setText("Units saved to file")

    # ---------------------------------------------------------------------------#
    # Write to register
    # ---------------------------------------------------------------------------#
    def updateWriteButton(self):
        if pollList:
            self.btnWrite.setEnabled(True)
            self.btnUnits.setEnabled(True)
        else:
            self.btnWrite.setEnabled(False)
            self.btnUnits.setEnabled(False)

    def writeToRegDelay(self):
        self.btnWrite.setEnabled(False)
        SensorThread.pollEn = False
        QTimer.singleShot(modbusTool.writeDelay, self.writeToReg)

    def writeToReg(self):
        # Struct arguments
        _uShort = 'H'
        _uInt = 'I'
        _uLong = 'L'
        _uByte = 'B'
        _uLongLong = 'Q'

        _bool = '?'
        _byte = 'b'
        _short = 'h'
        _int = 'i'
        _float = 'f'
        _double = 'd'
        _little_end = '<'
        _big_end = '>'

        global lenpollList
        valToWrite = []
        addrToWrite = []

        SensorThread.pollEn = False
        self.btnWrite.setEnabled(False)

        for row in list(range(0, lenpollList)):
            writeValue = self.tableWidget.item(row, modbusTool.colWrite)

            try:
                if float(eval(writeValue.text())):

                    if 'access' in pollList[row]:
                        if pollList[row]['access'] == "RO":
                            self.tableWidget.setItem(row, modbusTool.colWrite, QTableWidgetItem('Read Only Access'))
                            continue

                    writeEntry = eval(writeValue.text())

                    # Bool is single byte length
                    if pollList[row]['type'] == 'c_bool':
                        foo = struct.pack(_big_end+_bool, int(writeEntry))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _uByte
                        fi = struct.unpack(pack_id, foo)

                    else:
                        # uLong is defined as 4 word length, packs as a Python ulong long
                        if pollList[row]['type'] == 'c_ulong':
                            foo = struct.pack(_big_end+_uLongLong, int(writeEntry))

                        elif pollList[row]['type'] == 'c_uint':
                            foo = struct.pack(_big_end+_uInt, int(writeEntry))

                        elif pollList[row]['type'] == 'c_float':
                            foo = struct.pack(_big_end+_float, float(writeEntry))

                        elif pollList[row]['type'] == 'c_int':
                            foo = struct.pack(_big_end+_int, int(writeEntry))

                        elif pollList[row]['type'] == 'c_short':
                            foo = struct.pack(_big_end+_short, int(writeEntry))

                        elif pollList[row]['type'] == 'c_ubyte':
                            foo = struct.pack(_big_end+_uByte, int(writeEntry))

                        elif pollList[row]['type'] == 'c_ushort':
                            foo = struct.pack(_big_end+_uShort, int(writeEntry))

                        else:
                            self.tableWidget.setItem(row, modbusTool.colWrite, QTableWidgetItem('Invalid Type'))
                            continue

                        pack_id = _big_end + typeSizes[pollList[row]['type']] * _uShort
                        fi = struct.unpack(pack_id, foo)

                    if modbusTool.endian == modbusTool.endianCDAB:
                        reversedFi = [i for i in reversed(fi)]
                        fi = reversedFi

                    valToWrite.append(fi)
                    addrToWrite.append(pollList[row]['address'])
                    item = QTableWidgetItem('Write Pending (%s)' % writeEntry)
                    brush = QtGui.QBrush(QtGui.QColor(180, 180, 180))
                    brush.setStyle(QtCore.Qt.SolidPattern)
                    item.setBackground(brush)
                    self.tableWidget.setItem(row, modbusTool.colWrite, item)
                    self.tableWidget.resizeColumnToContents(modbusTool.colWrite)
                    pollList[row].update({'writepending' : True})

            except:
                continue

        SensorThread().writeToReg(valToWrite, addrToWrite)
        self.btnWrite.setEnabled(True)
        self.setPollRate()
        self.checkPollEn()
    # ---------------------------------------------------------------------------#
    # Updates table value field on modbus polling
    # ---------------------------------------------------------------------------#
    def updateValues(self, poll_value):
        global typeSizes
        global combobox
        # Struct arguments
        _uShort = 'H'
        _uInt = 'I'
        _uLong = 'L'
        _uByte = 'B'

        _bool = '?'
        _byte = 'b'
        _short = 'h'
        _int = 'i'
        _float = 'f'
        _double = 'd'
        _little_end = '<'
        _big_end = '>'

        if SensorThread.pollEn:

            for i in list(range(0, len(pollList))):
                try:
                    if poll_value[i] == '':
                        self.tableWidget.setItem(i, 0, QTableWidgetItem('Connect Error'))
                    else:
                        if modbusTool.endian == modbusTool.endianCDAB:
                            poll_value[i].reverse()

                        pack_id = _big_end + typeSizes[pollList[i]['type']] * _uShort
                        try:

                            if 'display' in pollList[i]:
                                if pollList[i]['display'] == 'Binary':
                                    formatStr = '{:b}'
                                elif pollList[i]['display'] == 'Hex':
                                    formatStr = '{:x}'
                                else:
                                    formatStr = '{:d}'
                            else:
                                formatStr = '{:d}'

                            if pollList[i]['type'] == 'c_bool':
                                pack_id = _big_end + typeSizes[pollList[i]['type']] * _uByte
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _bool, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_float':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _float, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue,
                                                         QTableWidgetItem('{:.10G}'.format(fi[0])))

                            elif pollList[i]['type'] == 'c_int':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _int, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'c_short':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _short, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'c_ubyte':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uByte, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'c_uint':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uInt, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            # NOT A PYTHON ULONG; Only used by still alive epoch time as a 64bit number
                            elif pollList[i]['type'] == 'c_ulong':
                                pack_id = _big_end + typeSizes[pollList[i]['type']] * _uByte
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uLong, foo)

                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_ushort':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uShort, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'vector2_t':
                                data = []
                                numEntries = list(range(0, int(pollList[i]['length'] / typeSizes[pollList[i]['type']])))
                                for j in numEntries:
                                    numEntries[j] = poll_value[i][0 + j * 4: 4 + j * 4]
                                for word in numEntries:
                                    foo = struct.pack(pack_id, *word)
                                    fi = struct.unpack(_big_end + _double, foo)
                                    data.append(fi[0])
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(data)))

                            self.tableWidget.setItem(i, modbusTool.colMsg, QTableWidgetItem(None))
                        # Struct.error exception if value is written too quickly for value to update
                        except struct.error:
                            self.tableWidget.setItem(i, modbusTool.colMsg, QTableWidgetItem('Type casting error'))
                            self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(poll_value[i])))
                            print('updateValues() pack error')
                            continue
                # If poll list has changed during value update, will result in error
                except IndexError:
                    print('Index Error')
                    pass
                except AttributeError:
                    print('Attr Error')
                    pass

    # ---------------------------------------------------------------------------#
    # Table entries updating
    # ---------------------------------------------------------------------------#
    def updateTable(self):
        global combobox
        combobox = [None] * len(pollList)
        _translate = QtCore.QCoreApplication.translate
        self.tableWidget.setRowCount(len(pollList))

        for entries in list(range(0, len(pollList))):
            item = QtWidgets.QTableWidgetItem()
            self.tableWidget.setVerticalHeaderItem(entries, item)
            item = self.tableWidget.verticalHeaderItem(entries)
            item.setText(_translate("MainWindow", pollList[entries]['varname']))
            item = QtWidgets.QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(entries, modbusTool.colRemove, item)
            self.tableWidget.setItem(entries, modbusTool.colRemove, QTableWidgetItem('   X'))

            # Set units column
            if 'units' in pollList[entries]:
                self.tableWidget.setItem(entries, modbusTool.colUnit, QTableWidgetItem(pollList[entries]['units']))

            # Set display columm
            if pollList[entries]['type'] not in ('c_float', 'c_bool', 'vector2_t'):
                combobox[entries] = QtWidgets.QComboBox()
                combobox[entries].addItem("Decimal")
                combobox[entries].addItem("Hex")
                combobox[entries].addItem("Binary")
                self.tableWidget.setCellWidget(entries,modbusTool.colDisp, combobox[entries])
                if 'display' in pollList[entries]:
                    if pollList[entries]['display'] == 'Hex':
                        combobox[entries].setCurrentIndex(modbusTool.hex)
                    elif pollList[entries]['display'] == 'Binary':
                        combobox[entries].setCurrentIndex(modbusTool.binary)
                    elif pollList[entries]['display'] == 'Decimal':
                        combobox[entries].setCurrentIndex(modbusTool.decimal)
                combobox[entries].currentIndexChanged.connect(self.setDispType)
            else:
                self.tableWidget.setItem(entries, modbusTool.colDisp, QTableWidgetItem(pollList[entries]['type']))

            # Set write pending columm
            if 'writepending' in pollList[entries]:
                if pollList[entries]['writepending']:
                    item = QtWidgets.QTableWidgetItem()
                    brush = QtGui.QBrush(QtGui.QColor(180, 180, 180))
                    brush.setStyle(QtCore.Qt.SolidPattern)
                    item.setBackground(brush)
                    self.tableWidget.setItem(entries, modbusTool.colWrite, item)

        self.tableWidget.resizeRowsToContents()
        self.updateWriteButton()

    def setDispType(self, dispType):
        dispComboBox = self.sender()
        parent = self.tableWidget.indexAt(dispComboBox.pos())
        pollList[parent.row()].update({'display' : dispComboBox.currentText()})

    def delTableEntry(self, row, col):
        SensorThread.pollEn = False
        global lenpollList
        if col == modbusTool.colRemove:
            self.tableWidget.removeRow(row)
            pollList.remove(pollList[row])
            self.updateTable()
            lenpollList = len(pollList)
            self.updateWriteButton()
        self.checkPollEn()

    def addTableEntry(self):
        SensorThread.pollEn = False
        global lenpollList
        baseNode = self.treeWidget.currentItem()
        if baseNode.childCount() == 0:
            varname_tree = baseNode.text(0)
            getParentNode = baseNode.parent()
            while getParentNode and getParentNode.text(0) != 'mbrecords':
                varname_tree = getParentNode.text(0) + '.' + varname_tree
                getParentNode = getParentNode.parent()
            for key, item in mbmapVar.items():
                if item['treename'] == varname_tree and item not in pollList:
                    pollList.append(item)
        lenpollList = len(pollList)
        self.updateTable()
        self.checkPollEn()

# ---------------------------------------------------------------------------#
# Gets list of dict values from key
# ---------------------------------------------------------------------------#
def get_values(dict_in, key_find):
    """
    :param dict_in: dict input
    :param key_find: Key string to search for
    :return: List of value entries with key matching key_find in dict_in
    """
    values_list = []

    def value_gen(d):
        for key, value in d.items():
            if key == key_find:
                yield value
            elif isinstance(value, dict):
                for id_val in value_gen(value):
                    yield id_val

    for values in value_gen(dict_in):
        values_list.append(values)

    return values_list

# ---------------------------------------------------------------------------#
# Dict merge function, d2 overrides d1
# ---------------------------------------------------------------------------#
def deepMerge(d1, d2, inconflict = lambda v1,v2 : v2) :
    for k in d2:
        if k in d1 :
            if isinstance(d1[k], dict) and isinstance(d2[k], dict) :
                deepMerge(d1[k], d2[k], inconflict)
            elif d1[k] != d2[k] :
                d1[k] = inconflict(d1[k], d2[k])
        else :
            d1[k] = d2[k]
    return d1

def main():
    global mbmap
    global mbmapVar

    global config_file
    global typeSizes

    try:
        with open('config\\config.json') as infile:
            config_file = json.load(infile)
            infile.close()
    except FileNotFoundError:
        input("Config.json not found. Press enter to continue...")
    try:
        with open('config\\units.json') as infile:
            units_file = json.load(infile)
            infile.close()
            config_file = deepMerge(config_file, units_file)
    except FileNotFoundError:
        pass

    # Get list of valid entries
    typeSizes = get_values(config_file, 'Sizes')[0]
    mbmap = get_values(config_file, 'mbrecord')
    for i in mbmap:
        if 'ignore' in i:
            mbmap.remove(i)
    mbmapVar = dict((d['varname'], dict(d, index=index)) for (index, d) in enumerate(mbmap))

    app = QtWidgets.QApplication(sys.argv)
    form = modbusTool()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()