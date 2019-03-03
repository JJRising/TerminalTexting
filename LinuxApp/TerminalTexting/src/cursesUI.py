'''
Created on Feb 25, 2019

@author: jj
'''

import xml.etree.ElementTree as ET
import curses
from src.colorSet import ColorSet
from src.scrollWindow import ScrollWindow
from src.textBar import TextBar
from src.tbox import Tbox
from queue import Queue
from src.inputThread import InputThread
from src.displayThread import DisplayThread
from src.bluetoothManager import BluetoothManager
import logging

STRINGS = ET.parse('res/strings.xml').getroot()
UUID = "56abddf0-d4d2-45c7-9b2b-7837582d436f"
SERVICE_NAME = "TerminalTexting"
COMMAND_WINDOW_MIN_HEIGHT = 3

def startUI():
    ui = UserInterface()
    curses.wrapper(ui.main)

def getString(name):
    for e in STRINGS.findall('string'):
        if e.get('name') == name:
            return e.text

class UserInterface():
    '''
    classdocs
    '''

    __STATE_START = "start"
    __STATE_CONNECT = "connect"
    __STATE_DISCONNECT = "disconnect"
    __STATE_LISTEN = "listen"
    __STATE_COMPOSE = "compse"
    __STATE_STOP = "stop"

    def __init__(self):
        '''
        Constructor
        '''
        self.state = self.__STATE_START
        self.newState = self.__STATE_START
        self.FSMBoolean = True
        self.inputThread = None
        self.displayThread = None
        self.bluetoothManager = None
        self.inputQueue = Queue()
        
        self.__stateFunc = { \
            self.__STATE_CONNECT: (self.__enterConnect, \
                                    self.__Connect, \
                                    self.__leaveConnect), \
            self.__STATE_DISCONNECT: (self.__enterDisconnect, \
                                       self.__Disconnect, \
                                       self.__leaveDisconnect), \
            self.__STATE_LISTEN: (self.__enterListen, \
                                   self.__Listen, \
                                   self.__leaveListen), \
            self.__STATE_COMPOSE: (self.__enterCompose, \
                                    self.__Compose, \
                                    self.__leaveCompose), \
            self.__STATE_STOP: (None, \
                                 self.__stop, \
                                 None)
            }
        
    def main(self, stdscr):
        try:
            self.__setup(stdscr)
            while self.FSMBoolean:
                logging.info(f"State: {self.state},   " \
                             f"NewState: {self.newState}")
                if self.__stateFunc[self.newState][0] != None:
                    self.__stateFunc[self.newState][0]()
                self.state = self.newState
                if self.__stateFunc[self.state][1] != None:
                    self.__stateFunc[self.state][1]()
                if self.__stateFunc[self.state][2] != None:
                    self.__stateFunc[self.state][2]()
        except KeyboardInterrupt:
            self.__stop()
            
    def __setup(self, stdscr):
        # Clear and refresh the screen
        stdscr.clear()
    
        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        # note
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        # error
        curses.init_pair(3, curses.COLOR_RED,    curses.COLOR_BLACK)
        # message recieved
        curses.init_pair(4, curses.COLOR_GREEN,  curses.COLOR_BLACK)
        # BluetoothManager
        curses.init_pair(5, curses.COLOR_BLUE,   curses.COLOR_BLACK)
        # options
        curses.init_pair(6, curses.COLOR_BLACK,  curses.COLOR_WHITE) 
        
        self.colorSet = ColorSet().set('standard', curses.color_pair(1)) \
                    .set('note', curses.color_pair(2)) \
                    .set('error', curses.color_pair(3)) \
                    .set('message recieved', curses.color_pair(4)) \
                    .set('bluetoothManager', curses.color_pair(5)) \
                    .set('options', curses.color_pair(6))
        
        # Get the hight and width of the main window and ctablealculate the
        # dimentions of the display and command windows
        (maxY, maxX) = stdscr.getmaxyx()
        commandHeight = int(maxY * 0.1)
        if commandHeight < COMMAND_WINDOW_MIN_HEIGHT:
            commandHeight = COMMAND_WINDOW_MIN_HEIGHT
        displayHeight = maxY - commandHeight - 6
        
        # Create the windows\
        dwin = curses.newwin(displayHeight, maxX - 2, 1, 1)
        iwin = curses.newwin(1, maxX, displayHeight + 2, 0)
        cwin = curses.newwin(commandHeight, maxX - 2, displayHeight + 4, 1)
        swin = curses.newwin(1, maxX, maxY - 1, 0)
        
        # Create the borders
        dwinBorderWin = curses.newwin(displayHeight + 2, maxX, 0, 0)
        dwinBorderWin.border()
        dwinBorderWin.refresh()
        cwinBorderWin = curses.newwin(commandHeight + 2, maxX, \
                                      displayHeight + 3, 0)
        cwinBorderWin.border()
        cwinBorderWin.refresh()
        
        dis = ScrollWindow(dwin)
        info = TextBar(iwin, self.colorSet.get('standard'))
        opt = TextBar(swin, self.colorSet.get('options'))
        self.tbox = Tbox(cwin, self.inputQueue)
        
        self.inputThread = InputThread(self.inputQueue, self.tbox)
        self.displayThread = DisplayThread(dis, info, self.tbox, opt)
        self.bluetoothManager = BluetoothManager(UUID, \
                                                 SERVICE_NAME, \
                                                 self.inputQueue)
        
        self.displayThread.printToDisplay("NOTE", \
                                          self.colorSet.get('note'), \
                                          "HEY, Listen!")
        
        self.newState = self.__STATE_CONNECT
        
    def __enterConnect(self):
        self.displayThread.printOptions(getString('options_connect'))
        self.displayThread.printStatus(getString('info_connect_options'))
    
    def __Connect(self):
        while self.newState == self.__STATE_CONNECT:
            myIn = self.inputQueue.get()
            outType = myIn[0]
            args = myIn[1]
            logging.info(outType)
            if not self.__standardHandlingMacro(outType, args):
                if outType == InputThread.KEYBOARD_INPUT:
                    if myIn[1] == curses.ascii.CAN: # ^X
                        self.newState = self.__STATE_STOP
                    elif myIn[1] == curses.ascii.SO: # ^N
                        logging.debug("connectAsServer")
                        logging.debug(self.bluetoothManager.state)
                        self.bluetoothManager.connectAsServer()
                    elif myIn[1] == curses.ascii.NAK: # ^U
                        # Client Connect
                        pass
                    else:
                        # Not relivent keystroke
                        pass
                elif outType == BluetoothManager.OUTPUT_CONNECTION_MADE:
                    self.newState = self.__STATE_LISTEN
                    self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    "Connection made with " \
                                    + args['device'].address)
                    return
                elif outType == BluetoothManager.OUTPUT_CONNECTION_FAILED:
                    self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['comment'] + " - " + \
                                    + str(args['error']))
                elif outType == BluetoothManager.OUTPUT_CONNECTION_LOST:
                    self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['comment'] + " - " + \
                                    + str(args['error']))
                else:
                    pass # Weird
    
    def __leaveConnect(self):
        pass
    
    def __enterListen(self):
        self.displayThread.printOptions(getString('options_listen'))
        self.displayThread.printStatus(getString('info_listen'))
    
    def __Listen(self):
        while self.newState == self.__STATE_LISTEN:
            myIn = self.inputQueue.get()
            outType = myIn[0]
            args = myIn[1]
            logging.info(outType)
            if not self.__standardHandlingMacro(outType, args):
                if outType == InputThread.KEYBOARD_INPUT:
                    if myIn[1] == curses.ascii.CAN: # ^X
                        self.newState = self.__STATE_DISCONNECT
                    elif myIn[1] == curses.ascii.SI: # ^O
                        # TODO: Reply function
                        self.newState = self.__STATE_COMPOSE
                    elif myIn[1] == curses.ascii.ENQ: # ^E
                        # TODO: Reply function
                        self.newState = self.__STATE_COMPOSE
                    else:
                        pass
                elif outType == BluetoothManager.OUTPUT_CONNECTION_LOST:
                    self.newState = self.__STATE_CONNECT
                    self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['comment'] + " - " \
                                    + str(args['error']))
                    return
                else:
                    pass # Weird
    
    def __leaveListen(self):
        pass
    
    def __enterDisconnect(self):
        self.displayThread.printOptions(getString('options_disconnect'))
        self.displayThread.printStatus(getString('info_disconnect'))
        self.bluetoothManager.disconnect()
    
    def __Disconnect(self):
        while self.newState == self.__STATE_DISCONNECT:
            myIn = self.inputQueue.get()
            outType = myIn[0]
            args = myIn[1]
            logging.info(outType)
            if not self.__standardHandlingMacro(outType, args):
                if outType == InputThread.KEYBOARD_INPUT:
                        pass
                elif outType == BluetoothManager.OUTPUT_CONNECTION_LOST:
                    self.newState = self.__STATE_CONNECT
                    self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['comment'] + " - " \
                                    + str(args['error']))
                    return
                elif outType == BluetoothManager.OUTPUT_DISCONNECTED:
                    self.newState = self.__STATE_CONNECT
                    self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['comment'])
                    return
                else:
                    pass # Weird
    
    def __leaveDisconnect(self):
        pass
    
    def __enterCompose(self):
        self.displayThread.printOptions(getString('options_compose'))
        self.displayThread.printStatus(getString('info_compose'))
        self.inputThread.suspend()
        self.tbox.edit()
    
    def __Compose(self):
        while self.newState == self.__STATE_COMPOSE:
            myIn = self.inputQueue.get()
            outType = myIn[0]
            args = myIn[1]
            logging.info(outType)
            if not self.__standardHandlingMacro(outType, args):
                if outType == BluetoothManager.OUTPUT_CONNECTION_LOST:
                    self.newState = self.__STATE_CONNECT
                    self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['comment'] + " - " + \
                                    + str(args['error']))
                    return
                elif outType == Tbox.OUTPUT_GATHER:
                    self.newState = self.__STATE_LISTEN
                    # TODO: Send
                elif outType == Tbox.OUTPUT_CANCEL:
                    self.newState = self.__STATE_LISTEN
                else:
                    pass # Weird
    
    def __leaveCompose(self):
        self.tbox.clear()
        self.inputThread.resume()
    
    def __standardHandlingMacro(self, outType, args):
        '''Handles the outputs of modules regardless of state
        Used to avoid rewirting the code.
        '''
        if outType == BluetoothManager.OUTPUT_RECEIVED_TEXT_MESSAGE:
            title = args['message'].contactName \
                    + " (" \
                    + args['message'].phoneNumber \
                    + ")"
            self.displayThread.printToDisplay(title, \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['message'].message)
        elif outType == BluetoothManager.OUTPUT_BLUETOOTH_MESSAGE:
            self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['message'])
            return True
        elif outType == BluetoothManager.OUTPUT_WRITE_SUCCESS:
            # TODO: Message Tracking
            return True
        elif outType == BluetoothManager.OUTPUT_WRITE_FAILED:
            # TODO: Message Tracking
            return True
        elif outType == BluetoothManager.OUTPUT_ERROR:
            self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['comment'] + " - " \
                                    + str(args['error']))
            return True
        elif outType == BluetoothManager.OUTPUT_NOTE:
            self.displayThread.printToDisplay("Bluetooth", \
                                    self.colorSet.get('bluetoothManager'), \
                                    args['note'])
            return True
        else:
            return False
        
    
    def __stop(self):
        self.displayThread.printToDisplay("Note", \
                                          self.colorSet.get('note'), \
                                          "Good Bye!\n[Press any key to exit]")
        self.inputThread.join()
        self.bluetoothManager.join()
        self.displayThread.join()
        self.FSMBoolean = False
        
            
            
            