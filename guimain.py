from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidget,QTableWidgetItem
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
from PyQt5.QtWidgets import (QTreeWidgetItem, QTreeWidget, QTreeView, QTableWidget, QTableWidgetItem, QSpinBox, QStatusBar, QDialog, QWidget, QPushButton, QLineEdit,
    QInputDialog, QApplication, QInputDialog, QLabel)
import logging
import struct

# TODO modularise sections into classes
x=1
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
                            regs_list[i] = (read_in)

                    except IndexError:
                        print('Read error')
                        pass
                regs = regs_list
                print('Register Values %s'%regs)
                print("------------------------------------------------------")
                self.regpoll.emit(regs)
            time.sleep(SensorThread.poll_rate)

# test class
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

    def __init__(self, parent = None):
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

class modbusTool(QtWidgets.QMainWindow, guidesign.Ui_MainWindow):

    disp_enable = True  # Enable for display update
    threadEn = False
    colValue = 0
    colUnit = 1
    colWrite = 2
    colRemove = 3
    colMsg = 4
    endianABCD = 0  # Big Endian Bytes, Reg 1 MSW
    endianCDAB = 1  # Big Endian Bytes, Reg 2 MSW

    endian = endianABCD # Endian for floats
    last_child = 0
    entryDict = {}
    def __init__(self, parent=None):
        super(modbusTool, self).__init__(parent)
        SensorThread().initIPaddress(SERVER_HOST)

        self.setupUi(self)
        self.createTree()
        self.updateTable()
        self.updateWriteButton()
        self.setPollRate()
        self.loadSettings()

        self.btnStop.setEnabled(False)
        self.btnStart.clicked.connect(self.startThread)
        self.treeWidget.doubleClicked.connect(self.addTableEntry)
        self.tableWidget.cellDoubleClicked.connect(self.delTableEntry)
        self.checkDebug.stateChanged.connect(self.debugModeToggle)
        self.btnWrite.clicked.connect(self.writeToReg)
        self.spinBoxPollRate.valueChanged.connect(self.setPollRate)
        self.comboBoxDataEncode.currentIndexChanged.connect(self.set_endian)
        self.btnUnits.clicked.connect(self.saveUnitsToFile)
        self.actionSetup.triggered.connect(self.initIP)
        self.actionSave.triggered.connect(self.saveView)
        self.actionLoad.triggered.connect(self.loadView)
        self.actionQuit.triggered.connect(self.quitApp)
        self.btnUpdate.clicked.connect(self.updateCommand)
        self.comboBoxDataEncode.setCurrentIndex(1)

    def updateCommandDelay(self):
        SensorThread.poll_rate = 1
        SensorThread.pollEn = False
        QTimer.singleShot(300, self.updateCommand)

    def updateCommand(self):
        SensorThread.commandWrite(self)
        #self.setPollRate()
        #if modbusTool.threadEn:
        #    self.updateUI()
        #SensorThread.pollEn = True
        #modbusTool.disp_enable = True
        #modbusTool.threadEn = True


    # ---------------------------------------------------------------------------#
    # Menu Bar actions
    # ---------------------------------------------------------------------------#
    def quitApp(self):
        QtCore.QCoreApplication.instance().exit()

    def saveView(self):
        text_file = open('settings.ini', "w")

        json.dump({'ViewList' : pollList}, text_file, indent=4, sort_keys=True)
        text_file.close()

        self.m_statusleft.setText("Settings saved!")


    def loadView(self):
        global pollList
        global lenpollList
        userInfile = self.openFileNameDialog()

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

    def loadSettings(self):
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


    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            return(fileName)

    def updateUI(self):
        modbusTool.disp_enable = True

        SensorThread.pollEn = True
        self.debugModeToggle()
        self.btnStart.setEnabled(False)
        self.btnStop.setEnabled(True)

    def initIP(self):

        text, ok = QInputDialog.getText(self, 'IP Address', 'Enter IP address')

        if ok:
            thing = str(text)
            print(str(text))
            SensorThread().initIPaddress(thing)

    # ---------------------------------------------------------------------------#
    # Creating tree widget from config.json
    # ---------------------------------------------------------------------------#
    def createTree(self):
        _translate = QtCore.QCoreApplication.translate
        self.treeWidget.clear()
        widget = QtWidgets.QTreeWidgetItem(self.treeWidget)
        widget.setText(0, _translate("MainWindow", 'mbrecords'))
        self.fill_item(widget, config_file)
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.setSortingEnabled(__sortingEnabled)
        self.treeWidget.expandToDepth(2)

    def fill_item(self, item, value):

        item.setExpanded(False)
        self.treeWidget.setExpandsOnDoubleClick(True)

        if type(value) is dict:
            for key, val in sorted(value.items()):
                if key == 'Types':
                    return
                if key == 'mbrecord':
                    child = modbusTool.last_child
                    varname_tree = str(val["name"])
                    getParentNode = child.parent()
                    while getParentNode and getParentNode.text(0) != 'mbrecords':
                        varname_tree = getParentNode.text(0) + '.' + varname_tree
                        getParentNode = getParentNode.parent()

                    modbusTool.entryDict.update({varname_tree : str(val["varname"])})
                    return
                child = QTreeWidgetItem()
                modbusTool.last_child = child
                child.setText(0, str(key))
                item.addChild(child)
                self.fill_item(child, val)

##
    ''' if type(value) is dict:
            for key, val in sorted(value.items()):

                if key == 'mbrecord':
                    child = QTreeWidgetItem()
                    #child = self.last_child #QTreeWidgetItem()
                    #self.last_child = child
                    child.setText(0, str(val["varname"]))
                    item.addChild(child)
                    #self.fill_item(child, val)
                    return
                child = QTreeWidgetItem()
                modbusTool.last_child = child
                child.setText(0, str(key))
                item.addChild(child)
                self.fill_item(child, val)
    ## Unnecessary section  ##
        elif type(value) is list:
            for val in value:
                child = QTreeWidgetItem()
                self.last_child = child
                item.addChild(child)
                if type(val) is dict:
                    child.setText(0, '[dict]')
                    self.fill_item(child, val)
                elif type(val) is list:
                    child.setText(0, '[list]')
                    self.fill_item(child, val)
                else:
                    child.setText(0, str(val))
                child.setExpanded(True)

        else:
            if not self.last_child:
                child = QTreeWidgetItem()
            else:
                child = self.last_child
            child.setText(0, child.text(0)+ " : " + str(value))
            item.addChild(child)
        ## ##'''




        ##
    # ---------------------------------------------------------------------------#
    # TODO Save units to config
    # ---------------------------------------------------------------------------#

    def genRecord(self, key, input):

        return input[key]

    def saveUnitsToFile(self):
        global lenpollList
        for row in list(range(0, lenpollList)):
            unitsValue = self.tableWidget.item(row, modbusTool.colUnit)

            try:
                pollList[row].update({'units': unitsValue.text()})
                configAddress = [key for key, value in modbusTool.entryDict.items() if value == pollList[row]['varname']][0]
                dict_ = config_file
                for i in configAddress.split('.'):
                    x = self.genRecord(i, dict_)
                    dict_ = x

                print(dict_)
            except AttributeError:
                continue




    # ---------------------------------------------------------------------------#
    # Starts polling on start clicked
    # ---------------------------------------------------------------------------#
    def startThread(self):
        SensorThread.pollEn = True
        self.debugModeToggle()
        modbusTool.disp_enable = True
        self.get_thread = SensorThread()
        self.get_thread.start()
        self.get_thread.regpoll.connect(self.updateValues)
        self.get_thread.pollCountSignal.connect(self.updatePollCount)
        self.btnStart.setEnabled(False)
        self.btnStop.setEnabled(True)
        self.btnStop.clicked.connect(self.pausedisplay)
        self.get_thread.finished.connect(self.done)
        modbusTool.threadEn = True


    def updatePollCount(self, pollCounter):
        self.m_statusright.setText("TX: %i" %(pollCounter))

       # self.statusBar.showMessage("TX: %i" %(pollCounter))

    # ---------------------------------------------------------------------------#
    # Stop button action
    # ---------------------------------------------------------------------------#
    def pausedisplay(self):
        modbusTool.threadEn = False
        SensorThread.pollEn = False
        modbusTool.disp_enable = False
        self.btnStop.setEnabled(False)
        self.btnStart.setEnabled(True)
        SensorThread().debugToggle(False)


    # ---------------------------------------------------------------------------#
    # Connects debug checkbox to debug mode toggle
    # ---------------------------------------------------------------------------#
    def debugModeToggle(self):
        if self.checkDebug.checkState():
            SensorThread().debugToggle(True)
        else:
            SensorThread().debugToggle(False)


    # ---------------------------------------------------------------------------#
    # Write to register
    # TODO Write access check
    # ---------------------------------------------------------------------------#
    def updateWriteButton(self):
        if pollList:
            self.btnWrite.setEnabled(True)
            self.btnUnits.setEnabled(True)
        else:
            self.btnWrite.setEnabled(False)
            self.btnUnits.setEnabled(False)

    def writeToRegDelay(self):
        SensorThread.poll_rate = 1
        SensorThread.pollEn = False
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
                        fi=reversedFi
                    valToWrite.append(fi)

                    self.tableWidget.setItem(row, modbusTool.colMsg, QTableWidgetItem('Write Success (%s)' % writeValue.text()))
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
        if modbusTool.threadEn:
            self.updateUI()

    # ---------------------------------------------------------------------------#
    # Updates table value field on modbus polling
    # ---------------------------------------------------------------------------#
    def set_endian(self, endianVal):
            modbusTool.endian = endianVal


    def setPollRate(self):
        SensorThread.poll_rate = self.spinBoxPollRate.value()


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

        if modbusTool.disp_enable:

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
                                print(pack_id)
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _float, foo)
                                print(fi[0], ' ', _big_end + _bool, ' ' , poll_value[i])

                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem('{:.9f}'.format(fi[0])))
                                print(fi[0])
                            elif pollList[i]['type'] == 'c_int':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end + _int, foo)
                                self.tableWidget.setItem(i, modbusTool.colValue, QTableWidgetItem(str(fi[0])))

                            elif pollList[i]['type'] == 'c_short':
                                foo = struct.pack(pack_id, *poll_value[i])
                                fi = struct.unpack(_big_end+ _short, foo)
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
                                numEntries = list(range(0,int(pollList[i]['length'] / typeSizes[pollList[i]['type']])))
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
                self.tableWidget.setItem(entries, modbusTool.colUnit,QTableWidgetItem(pollList[entries]['units']))

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
                getParentNode =  getParentNode.parent()

            for entry in mbmap:
                if modbusTool.entryDict[varname_tree] == entry['varname'] and entry not in pollList:
                    pollList.append(entry)
        lenpollList = len(pollList)
        self.updateTable()




    # ---------------------------------------------------------------------------#
    # Thread finished action
    # ---------------------------------------------------------------------------#
    def done(self):
        self.btnStop.setEnabled(False)
        self.btnStart.setEnabled(True)


    # ---------------------------------------------------------------------------#
    # Print message in the message column
    # ---------------------------------------------------------------------------#
    def printMsg(self, row, msg):
        self.tableWidget.setItem(row, modbusTool.colMsg, QTableWidgetItem(msg))


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
