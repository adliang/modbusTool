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

x = 0
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

    def readSettings(self, addr, length):
        return SensorThread.c.read_holding_registers(addr, length)

    def writeSettings(self, addr, data):
        SensorThread.c.write_multiple_registers(addr, data)

    def writeToReg(self, writeArray, addrArray):
        print(writeArray)
        print('addrestowrite')
        print(addrArray)
        for i in range(len(writeArray)):
            if writeArray[i]:
                try:
                    SensorThread.c.write_multiple_registers(addrArray[i], writeArray[i])

                    print('Write Success (%s %s)' % (addrArray[i],writeArray[i]))
                except ValueError:
                    print('Write error')

    def commandButton(self, command):
        SensorThread.c.write_multiple_registers(1000, [command, 0])

    def debugToggle(self, state):
        SensorThread.c.debug(state)

    def setPollRate(self, pollRate):
        SensorThread.poll_rate = pollRate

    def run(self):
        global lenpollList
        while True:
            if  SensorThread.pollEn:
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
                    print('Register Values %s' % regs)
                    print("------------------------------------------------------")
                    self.regpoll.emit(regs)
                time.sleep(SensorThread.poll_rate)
            else:
                continue

### test class
class NewWindow(QtWidgets.QMainWindow):
    def __init__(self, text):
        super(NewWindow, self).__init__()
        self.message = text
        self.initUI()

    def initUI(self):
        self.resize(250, 100)
        self.label = QtWidgets.QLabel(self)
        self.label.setText(self.message)
        self.dialog = QtWidgets.QTextEdit(self)
##
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
    entryDict = {}

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

        self.btnUpdate.clicked.connect(self.commandUpdateBtn)
        self.btnStop.clicked.connect(self.commandStopBtn)
        self.btnStart.clicked.connect(self.commandStartBtn)
        self.btnReset.clicked.connect(self.commandResetBtn)
        self.btnLoadDefaults.clicked.connect(self.commandLoadDefaultsBtn)
        self.btnTest.clicked.connect(self.commandTestBtn)

        self.actionSetup.triggered.connect(self.initIP)
        self.actionSave_Settings.triggered.connect(self.saveSettings)
        self.actionLoad_Settings.triggered.connect(self.loadSettings)
        self.actionSave_View_List.triggered.connect(self.saveViewList)
        self.actionLoad_View_List.triggered.connect(self.loadViewList)
        self.actionQuit.triggered.connect(self.quitApp)

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
                settingReading = SensorThread().readSettings(i['address'], typeSizes[i['type']])
                i.update({'value' : settingReading})
                saveSettingsList.update({i['varname']: i})

        text_file = open('settings.ini', "w")
        json.dump({'Settings':saveSettingsList}, text_file, indent=4, sort_keys=True)
        text_file.close()

        self.checkPollEn()
        self.m_statusleft.setText("Setting Saved!")

    def loadSettings(self):
        def openFileNameDialog():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self, "Load Settings", "",
                                                      "Settings Files (*.ini);; All Files (*)", options=options)
            if fileName:
                return fileName

        userInfile = openFileNameDialog()

        def build_dict(seq, key):
            return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))

        try:
            with open(userInfile) as infile:
                settings_data = json.load(infile)
                infile.close()
                settings_data = settings_data['Settings']

        except:
            self.m_statusleft.setText("Invalid Settings File")
            return

        mbmapByVarname = build_dict(mbmap, 'varname')
        for key in list(settings_data.keys()):
            if key in mbmapByVarname:
                if settings_data[key]['type'] == mbmapByVarname[key]['type']:
                    SensorThread().writeSettings(mbmapByVarname[key]['address'], settings_data[key]['value'])

        self.m_statusleft.setText("Setting Loaded!")

    # ---------------------------------------------------------------------------#
    # Command buttons
    # ---------------------------------------------------------------------------#
    def commandStopBtn(self):
        SensorThread.pollEn = False
        SensorThread().commandButton(1)
        self.textBrowserCommand.setText("Stop Sent")
        print('Stop Command Sent')
        self.checkPollEn()

    def commandResetBtn(self):
        SensorThread.pollEn = False
        SensorThread().commandButton(2)
        self.textBrowserCommand.setText("Reset Sent")
        print('Reset Command Sent')
        self.checkPollEn()

    def commandStartBtn(self):
        SensorThread.pollEn = False
        SensorThread().commandButton(4)
        self.textBrowserCommand.setText("Start Sent")
        print('Start Command Sent')
        self.checkPollEn()

    def commandTestBtn(self):
        SensorThread.pollEn = False
        SensorThread().commandButton(8)
        self.textBrowserCommand.setText("Test Sent")
        print('Test Command Sent')
        self.checkPollEn()

    def commandLoadDefaultsBtn(self):
        SensorThread.pollEn = False
        SensorThread().commandButton(16)
        self.textBrowserCommand.setText("Load Defaults Sent")
        print('Load Defaults Command Sent')
        self.checkPollEn()

    def commandUpdateBtn(self):
        SensorThread.pollEn = False
        SensorThread().commandButton(32)
        self.textBrowserCommand.setText("Update Sent")
        print('Update Command Sent')
        self.checkPollEn()

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
                        child = modbusTool.last_child
                        varname_tree = str(val["name"])
                        getParentNode = child.parent()
                        while getParentNode and getParentNode.text(0) != 'mbrecords':
                            varname_tree = getParentNode.text(0) + '.' + varname_tree
                            getParentNode = getParentNode.parent()
                        modbusTool.entryDict.update({varname_tree: str(val["varname"])})

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
    # Initialises viewilist.ini view list
    # ---------------------------------------------------------------------------#
    def initViewList(self):
        global pollList
        global lenpollList
        try:
            with open('viewlist.ini') as infile:
                settings_data = json.load(infile)
                infile.close()
                pollList = settings_data['ViewList']
                self.m_statusleft.setText("View list loaded")
                lenpollList = len(pollList)
                self.updateTable()
        except:
            self.m_statusleft.setText("No settings file found...")

    # ---------------------------------------------------------------------------#
    # Menu Bar actions
    # ---------------------------------------------------------------------------#
    # Settings menu button
    def initIP(self):
        text, ok = QInputDialog.getText(self, 'IP Address', 'Enter IP address')
        if ok:
            thing = str(text)
            SensorThread().initIPaddress(thing)
            self.m_statusmid.setText("IP: %s" % thing)

    # Save view list menu button
    def saveViewList(self):
        text_file = open('viewlist.ini', "w")
        json.dump({'ViewList': pollList}, text_file, indent=4, sort_keys=True)
        text_file.close()
        self.m_statusleft.setText("View list saved!")



    # Load view list menu button
    def loadViewList(self):
        global pollList
        global lenpollList

        def openFileNameDialog():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self, "Load View List", "",
                                                      "View List Files (*.ini);; All Files (*)", options=options)
            if fileName:
                return fileName

        userInfile = openFileNameDialog()
        try:
            with open(userInfile) as infile:
                viewListData = json.load(infile)
                infile.close()
                pollList = viewListData['ViewList']
                self.m_statusleft.setText("View list loaded")
                lenpollList = len(pollList)
                self.updateTable()
        except:
            self.m_statusleft.setText("Invalid view list file")

    # Quit menu button
    def quitApp(self):
        QtCore.QCoreApplication.instance().exit()

    # ---------------------------------------------------------------------------#
    # Thread finished action
    # ---------------------------------------------------------------------------#
    def done(self):
        self.checkBoxPoll.setCheckState(0)


    # ---------------------------------------------------------------------------#
    # Start button action - Starts polling
    # ---------------------------------------------------------------------------#
    def checkPollEn(self):
        if self.checkBoxPoll.checkState():
            SensorThread.pollEn = True
            self.debugModeToggle()
        else:
            SensorThread.pollEn = False
            SensorThread().debugToggle(False)


    # ---------------------------------------------------------------------------#
    # Save units button action
    # ---------------------------------------------------------------------------#
    def saveUnitsToFile(self):
        global lenpollList
        for row in list(range(0, lenpollList)):
            unitsValue = self.tableWidget.item(row, modbusTool.colUnit)

            try:
                pollList[row].update({'units': unitsValue.text()})
                #configAddress = [key for key, value in modbusTool.entryDict.items() if value == pollList[row]['varname']][0]
                #dict_ = config_file
                #pprint(configAddress.split('.')[1:])
                #x_temp = {configAddress.split('.')[1]: None}
                #for i in range(1 , 1+len(configAddress.split('.')[1:])):
                    #x_temp.update({ configAddress.split('.')[i-1] : ({configAddress.split('.')[i]: None}) })
                    #x = dict_
                    # [i]
                    #dict_ = x

                #pprint(x_temp)
            except AttributeError:
                continue


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
        SensorThread.pollEn = False

        SensorThread.poll_rate = 1
        QTimer.singleShot(300, self.writeToReg)

    def writeToReg(self):
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

        global lenpollList
        valToWrite = []
        addrToWrite = []

        self.btnWrite.setEnabled(False)

        for row in list(range(0, lenpollList)):
            writeValue = self.tableWidget.item(row, modbusTool.colWrite)

            if writeValue:
                try:
                    if pollList[row]['type'] == 'c_bool':
                        foo = struct.pack('>?', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _uByte
                        fi = struct.unpack(pack_id, foo)

                    elif pollList[row]['type'] == 'c_uint':
                        foo = struct.pack('>I', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _uShort
                        fi = struct.unpack(pack_id, foo)

                    elif pollList[row]['type'] == 'c_float':
                        foo = struct.pack('>f', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _short
                        fi = struct.unpack(pack_id, foo)

                    elif pollList[row]['type'] == 'c_int':
                        foo = struct.pack('>i', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _short
                        fi = struct.unpack(pack_id, foo)

                    elif pollList[row]['type'] == 'c_short':
                        foo = struct.pack('>h', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _short
                        fi = struct.unpack(pack_id, foo)

                    elif pollList[row]['type'] == 'c_ubyte':
                        foo = struct.pack('>B', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _uShort
                        fi = struct.unpack(pack_id, foo)

                    elif pollList[row]['type'] == 'c_ulong':
                        foo = struct.pack('>L', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _uShort
                        fi = struct.unpack(pack_id, foo)

                    elif pollList[row]['type'] == 'c_ushort':
                        foo = struct.pack('>H', int(writeValue.text()))
                        pack_id = '>' + typeSizes[pollList[row]['type']] * _uShort
                        fi = struct.unpack(pack_id, foo)

                    if modbusTool.endian == modbusTool.endianCDAB:
                        reversedFi = [i for i in reversed(fi)]
                        fi = reversedFi
                    valToWrite.append(fi)

                    self.tableWidget.setItem(row, modbusTool.colMsg,
                                             QTableWidgetItem('Write Pending (%s)' % writeValue.text()))
                    self.tableWidget.setItem(row, modbusTool.colWrite, QTableWidgetItem(None))
                    item = QtWidgets.QTableWidgetItem()
                    brush = QtGui.QBrush(QtGui.QColor(180, 180, 180))
                    brush.setStyle(QtCore.Qt.SolidPattern)
                    item.setBackground(brush)
                    self.tableWidget.setItem(row, modbusTool.colWrite, item)
                except ValueError:
                    self.tableWidget.setItem(row, modbusTool.colMsg, QTableWidgetItem(''))
                    continue

            else:
                valToWrite.append(None)
            addrToWrite.append(pollList[row]['address'])
        SensorThread().writeToReg(valToWrite, addrToWrite)
        self.btnWrite.setEnabled(True)
        self.setPollRate()
        self.checkPollEn()
    # ---------------------------------------------------------------------------#
    # Updates table value field on modbus polling
    # ---------------------------------------------------------------------------#
    def set_endian(self, endianVal):
        modbusTool.endian = endianVal

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
                                dispBox = self.tableWidget.cellWidget(i, modbusTool.colDisp)
                                if dispBox.currentText() == 'Binary':
                                    formatStr = '{:b}'
                                elif dispBox.currentText() == 'Hex':
                                    formatStr = '{:x}'
                                else:
                                    formatStr = '{:d}'
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'c_short':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _short, foo)
                                dispBox = self.tableWidget.cellWidget(i, modbusTool.colDisp)
                                if dispBox.currentText() == 'Binary':
                                    formatStr = '{:b}'
                                elif dispBox.currentText() == 'Hex':
                                    formatStr = '{:x}'
                                else:
                                    formatStr = '{:d}'
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'c_ubyte':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uByte, foo)
                                dispBox = self.tableWidget.cellWidget(i, modbusTool.colDisp)
                                if dispBox.currentText() == 'Binary':
                                    formatStr = '{:b}'
                                elif dispBox.currentText() == 'Hex':
                                    formatStr = '{:x}'
                                else:
                                    formatStr = '{:d}'
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'c_uint':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uInt, foo)
                                dispBox = self.tableWidget.cellWidget(i, modbusTool.colDisp)
                                if dispBox.currentText() == 'Binary':
                                    formatStr = '{:b}'
                                elif dispBox.currentText() == 'Hex':
                                    formatStr = '{:x}'
                                else:
                                    formatStr = '{:d}'
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(formatStr.format(fi[0])))

                            elif pollList[i]['type'] == 'c_ulong':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _double, foo)

                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_ushort':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uShort, foo)
                                dispBox = self.tableWidget.cellWidget(i, modbusTool.colDisp)
                                if dispBox.currentText() == 'Binary':
                                    formatStr = '{:b}'
                                elif dispBox.currentText() == 'Hex':
                                    formatStr = '{:x}'
                                else:
                                    formatStr = '{:d}'
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

                        # Struct.error exception if value is written too quickly for value to update
                        except struct.error:
                            self.tableWidget.setItem(i, modbusTool.colMsg, QTableWidgetItem('Unit conversion mismatch'))
                            self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(poll_value[i])))
                            print('struct Error')
                            continue
                # If poll list has changed during value update, will result in error
                except IndexError:
                    print('Index Error')
                    pass
                # TODO fix ?
                except AttributeError:
                    print('Attr Error')
                    pass
        self.tableWidget.resizeColumnsToContents()

    # ---------------------------------------------------------------------------#
    # Table entries updating
    # ---------------------------------------------------------------------------#
    def updateTable(self):
        global combobox
        _translate = QtCore.QCoreApplication.translate
        self.tableWidget.setRowCount(len(pollList))
        combobox = [None] * len(pollList)
        for entries in list(range(0, len(pollList))):
            item = QtWidgets.QTableWidgetItem()
            self.tableWidget.setVerticalHeaderItem(entries, item)
            item = self.tableWidget.verticalHeaderItem(entries)
            item.setText(_translate("MainWindow", pollList[entries]['varname']))
            item = QtWidgets.QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(entries, modbusTool.colRemove, item)
            self.tableWidget.setItem(entries, modbusTool.colRemove, QTableWidgetItem('   X'))
            if 'units' in pollList[entries]:
                self.tableWidget.setItem(entries, modbusTool.colUnit, QTableWidgetItem(pollList[entries]['units']))
            if pollList[entries]['type'] != 'c_float' and pollList[entries]['type'] != 'c_bool' and pollList[entries]['type'] != 'vector2_t':
                combobox[entries] = QtWidgets.QComboBox()
                combobox[entries].addItem("Decimal")
                combobox[entries].addItem("Hex")
                combobox[entries].addItem("Binary")
                self.tableWidget.setCellWidget(entries,modbusTool.colDisp, combobox[entries])
            if pollList[entries]['type'] == 'c_float':
                self.tableWidget.setItem(entries, modbusTool.colDisp, QTableWidgetItem('Float'))
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.updateWriteButton()

    def delTableEntry(self, row, col):
        global lenpollList
        if col == modbusTool.colRemove:
            self.tableWidget.removeRow(row)
            pollList.remove(pollList[row])
            self.updateTable()
            lenpollList = len(pollList)
            self.updateWriteButton()

    def addTableEntry(self):
        global lenpollList
        getSelected = self.treeWidget.currentItem()
        baseNode = getSelected
        if baseNode.childCount() == 0:
            varname_tree = baseNode.text(0)
            getParentNode = baseNode.parent()
            while getParentNode and getParentNode.text(0) != 'mbrecords':
                varname_tree = getParentNode.text(0) + '.' + varname_tree
                getParentNode = getParentNode.parent()

            entryVarname = modbusTool.entryDict[varname_tree]
            if mbmapVar[entryVarname] not in pollList:
                pollList.append(mbmapVar[entryVarname])

            #if modbusTool.entryDict[varname_tree] == entry['varname'] and entry not in pollList:
             #   pollList.append(entry)
        lenpollList = len(pollList)
        self.updateTable()


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


def main():
    global mbmap
    global mbmapVar

    global config_file
    global typeSizes
    global user_file

    try:
        with open('config\config.json') as infile:
            config_file = json.load(infile)
            infile.close()
    except FileNotFoundError:
        input("Config.json not found. Press enter to continue...")
    try:
        with open('config\config-user.json') as infile:
            user_file = json.load(infile)
            infile.close()
    except FileNotFoundError:
        input("Config-user.json not found. Press enter to continue...")

    # Get list of valid entries
    typeSizes = get_values(config_file, 'Sizes')[0]
    mbmap = get_values(config_file, 'mbrecord')
    for i in mbmap:
        if 'ignore' in i:
            mbmap.remove(i)

    mbmapVar = dict((d['varname'], dict(d, index=index)) for (index, d) in enumerate(mbmap))
    pprint(mbmapVar)
    app = QtWidgets.QApplication(sys.argv)
    form = modbusTool()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
