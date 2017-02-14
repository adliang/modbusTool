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
    writeSuccess = pyqtSignal(bool)
    poll_rate = 1
    pollEn = True
    c = 0
    pollCountSignal = pyqtSignal(int)
    pollCount = 0

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def initIPaddress(self, ip):

        SensorThread.c = ModbusClient(host=ip, port=SERVER_PORT, auto_open=True, auto_close=True)

    def commandWrite(self):
        SensorThread.c.write_multiple_registers(1000, [32, 0])

    def writeToReg(self, writeArray, addrArray):
        print(writeArray)
        print('addrestowrite')
        print(addrArray)
        for i in range(len(writeArray)):
            if writeArray[i]:

                try:
                    SensorThread.c.write_multiple_registers(addrArray[i], writeArray[i])
                except ValueError:
                    self.writeSuccess.emit(False)
                    print('Write error')

    def debugToggle(self, state):
        SensorThread.c.debug(state)

    def setPollRate(self, pollRate):
        SensorThread.poll_rate = pollRate

    def run(self):
        global lenpollList
        while SensorThread.pollEn:
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


class ImageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.picture = QtGui.QPixmap('tux.jpeg')

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.picture)


class ImgWidget1(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(ImgWidget1, self).__init__(parent)

        pic = QtGui.QPixmap('mosbuus.png')
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setPixmap(pic)


##

class modbusTool(QtWidgets.QMainWindow, guidesign.Ui_MainWindow):
    # Table Columns
    colValue = 0
    colUnit = 1
    colWrite = 2
    colRemove = 3
    colMsg = 4

    endianABCD = 0  # Big Endian Bytes, Reg 1 MSW
    endianCDAB = 1  # Big Endian Bytes, Reg 2 MSW
    threadStarted = 0
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
        self.btnStop.setEnabled(False)

        self.checkDebug.stateChanged.connect(self.debugModeToggle)
        self.spinBoxPollRate.valueChanged.connect(self.setPollRate)
        self.comboBoxDataEncode.currentIndexChanged.connect(self.set_endian)
        self.comboBoxDataEncode.setCurrentIndex(1)

        self.btnUnits.clicked.connect(self.saveUnitsToFile)
        self.btnStart.clicked.connect(self.startThread)
        self.btnWrite.clicked.connect(self.writeToReg)
        self.btnStop.clicked.connect(self.pausedisplay)
        self.treeWidget.doubleClicked.connect(self.addTableEntry)
        self.tableWidget.cellDoubleClicked.connect(self.delTableEntry)

        self.actionSetup.triggered.connect(self.initIP)
        self.actionSave_View_List.triggered.connect(self.saveViewList)
        self.actionLoad_View_List.triggered.connect(self.loadViewList)
        self.actionQuit.triggered.connect(self.quitApp)

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
    # Initialises settings.ini view list
    # ---------------------------------------------------------------------------#
    def initViewList(self):
        global pollList
        global lenpollList
        try:
            with open('settings.ini') as infile:
                settings_data = json.load(infile)
                infile.close()
                pollList = settings_data['ViewList']
                self.m_statusleft.setText("Setting loaded")
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
            print(str(text))
            SensorThread().initIPaddress(thing)

    # Save view list menu button
    def saveViewList(self):
        text_file = open('settings.ini', "w")
        json.dump({'ViewList': pollList}, text_file, indent=4, sort_keys=True)
        text_file.close()
        self.m_statusleft.setText("Settings saved!")

    # Load view list menu button
    def loadViewList(self):
        global pollList
        global lenpollList

        def openFileNameDialog():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self, "Load Settings View", "",
                                                      "Settings Files (*.ini);; All Files (*)", options=options)
            if fileName:
                return fileName

        userInfile = openFileNameDialog()
        try:
            with open(userInfile) as infile:
                settings_data = json.load(infile)
                infile.close()
                pollList = settings_data['ViewList']
                self.m_statusleft.setText("Setting loaded")
                lenpollList = len(pollList)
                self.updateTable()
        except:
            self.m_statusleft.setText("Invalid settings file")

    # Quit menu button
    def quitApp(self):
        QtCore.QCoreApplication.instance().exit()

    # ---------------------------------------------------------------------------#
    # Thread finished action
    # ---------------------------------------------------------------------------#
    def done(self):
        self.btnStop.setEnabled(False)
        self.btnStart.setEnabled(True)

    # ---------------------------------------------------------------------------#
    # Start button action - Starts polling
    # ---------------------------------------------------------------------------#
    def startThread(self):
        SensorThread.pollEn = True
        self.debugModeToggle()
        if not modbusTool.threadStarted:
            print('fsusfudfs')
            self.get_thread = SensorThread()
            self.get_thread.start()
            self.get_thread.regpoll.connect(self.updateValues)
            self.get_thread.pollCountSignal.connect(self.updatePollCount)
            self.get_thread.finished.connect(self.done)
            modbusTool.threadStarted = 1
        else:
            print('SAUSABSDBDASs')
        self.btnStart.setEnabled(False)
        self.btnStop.setEnabled(True)


    # ---------------------------------------------------------------------------#
    # Stop button action
    # ---------------------------------------------------------------------------#
    def pausedisplay(self):
        SensorThread.pollEn = False
        SensorThread().debugToggle(False)

        self.btnStop.setEnabled(False)
        self.btnStart.setEnabled(True)


    # ---------------------------------------------------------------------------#
    # Save units button action
    # TODO
    # ---------------------------------------------------------------------------#
    def saveUnitsToFile(self):
        global lenpollList
        for row in list(range(0, lenpollList)):
            unitsValue = self.tableWidget.item(row, modbusTool.colUnit)

            try:
                pollList[row].update({'units': unitsValue.text()})
                configAddress = [key for key, value in modbusTool.entryDict.items() if value == pollList[row]['varname']][0]
                dict_ = config_file
                for i in configAddress.split('.'):
                    x = dict_[i]
                    dict_ = x
                print(dict_)
            except AttributeError:
                continue


    # ---------------------------------------------------------------------------#
    # Write to register
    # ---------------------------------------------------------------------------#
    def updateUI(self):
        SensorThread.pollEn = True
        self.debugModeToggle()
        self.btnStart.setEnabled(False)
        self.btnStop.setEnabled(True)

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
        QTimer.singleShot(400, self.writeToReg)

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
                        foo = struct.pack('>L', int(writeValue.text()))
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
                                             QTableWidgetItem('Write Success (%s)' % writeValue.text()))
                    self.tableWidget.setItem(row, modbusTool.colWrite, QTableWidgetItem(None))
                except ValueError:
                    self.tableWidget.setItem(row, modbusTool.colMsg, QTableWidgetItem(''))
                    continue

            else:
                valToWrite.append(None)
            addrToWrite.append(pollList[row]['address'])
        SensorThread().writeToReg(valToWrite, addrToWrite)
        self.btnWrite.setEnabled(True)
        self.setPollRate()
        if SensorThread.pollEn:
            self.updateUI()

    # ---------------------------------------------------------------------------#
    # Updates table value field on modbus polling
    # ---------------------------------------------------------------------------#
    def set_endian(self, endianVal):
        modbusTool.endian = endianVal

    def updateValues(self, poll_value):
        global typeSizes
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
                    if poll_value[i] == 'No Value Read':
                        self.tableWidget.setItem(i, 0, QTableWidgetItem(str(poll_value[i])))
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
                                                         QTableWidgetItem('{:.9f}'.format(fi[0])))

                            elif pollList[i]['type'] == 'c_int':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _int, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_short':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _short, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_ubyte':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uByte, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_uint':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uInt, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_ulong':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _double, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_ushort':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _uShort, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

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
                            print('struct Error')
                            continue
                # If poll list has changed during value update, will result in error
                except IndexError:
                    pass
                # TODO fix ?
                except AttributeError:
                    pass
        self.tableWidget.resizeColumnsToContents()

    # ---------------------------------------------------------------------------#
    # Table entries updating
    # ---------------------------------------------------------------------------#
    def updateTable(self):
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
            if 'units' in pollList[entries]:
                self.tableWidget.setItem(entries, modbusTool.colUnit, QTableWidgetItem(pollList[entries]['units']))

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
            # # Code if varname matches tree address
            getParentNode = baseNode.parent()
            while getParentNode and getParentNode.text(0) != 'mbrecords':
                varname_tree = getParentNode.text(0) + '.' + varname_tree
                getParentNode = getParentNode.parent()

            for entry in mbmap:
                if modbusTool.entryDict[varname_tree] == entry['varname'] and entry not in pollList:
                    pollList.append(entry)
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

    app = QtWidgets.QApplication(sys.argv)
    form = modbusTool()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
