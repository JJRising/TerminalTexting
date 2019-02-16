'''
Created on Jan 15, 2019

@author: jj
'''

import xml.etree.ElementTree as ET
from src import bluetoothManager, \
                bluetoothMessageFormatter, \
                threadedTextBox, \
                displayWindow
from threading import Event, Lock
import curses
import logging

STRINGS = ET.parse('res/strings.xml').getroot()
UUID = "56abddf0-d4d2-45c7-9b2b-7837582d436f"

def getString(name):
    for e in STRINGS.findall('string'):
        if e.get('name') == name:
            return e.text
    
class UI():
    
    COMMAND_WINDOW_MIN_HEIGHT = 3
    STATE = {'start': "Start", \
              'connect': "Connect", \
              'disconnect': "Disconnect", \
              'listen': "Listen", \
              'compose': "Compose", \
              'stop': "Stop"}
    
    def __init__(self):
        self.state = self.STATE['start']
        self.newState = self.STATE['start']
        self.dis = None
        self.disThread = None
        self.info = None
        self.opt = None
        self.tbox = None
        self.btm = None # BluetoothManager
        self.quitFlag = False
        self.FSMBoolean = True
        self.uiWaitFlag = None
        self.disQueue = None
        self.lastMessageSender = None
        self.disconnectEvent = Event()
        self.displayLock = Lock()
        
        
        self.__stateFunc = { \
            self.STATE['start']: (None,  \
                                  self.__start, \
                                  None), \
            self.STATE['connect']: (self.__enterConnect, \
                                    self.__Connect, \
                                    self.__leaveConnect), \
            self.STATE['disconnect']: (self.__enterDisconnect, \
                                       self.__Disconnect, \
                                       self.__leaveDisconnect), \
            self.STATE['listen']: (self.__enterListen, \
                                   self.__Listen, \
                                   self.__leaveListen), \
            self.STATE['compose']: (self.__enterCompose, \
                                    self.__Compose, \
                                    self.__leaveCompose), \
            self.STATE['stop']: (None, \
                                 self.__stop, \
                                 None)
            }
        
    def main(self, stdscr):
        try:
            logging.info("Curses started")
            self.__start(stdscr)
            while self.FSMBoolean:
                logging.info("State: " + str(self.state) + " New State: " \
                             + str(self.newState))
                if self.newState != self.state:
                    if self.__stateFunc[self.newState][0] != None:
                        self.__stateFunc[self.newState][0]()
                self.state = self.newState
                if self.__stateFunc[self.newState][1] != None:
                    self.__stateFunc[self.state][1]()
                if self.newState != self.state:
                    if self.__stateFunc[self.state][2] != None:
                        self.__stateFunc[self.state][2]()
        except KeyboardInterrupt:
            self.__stop()

    def __start(self, stdscr):        
        # Clear and refresh the screen
        stdscr.clear()
        stdscr.refresh()
    
        # Start colors in curses
        curses.start_color()
        # note
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        # error
        curses.init_pair(2, curses.COLOR_RED,    curses.COLOR_BLACK)
        # message recieved
        curses.init_pair(3, curses.COLOR_GREEN,  curses.COLOR_BLACK)
        # BluetoothManager
        curses.init_pair(4, curses.COLOR_BLUE,   curses.COLOR_BLACK)
        # options
        curses.init_pair(5, curses.COLOR_BLACK,  curses.COLOR_WHITE) 
        
        self.colorSet = displayWindow.ColorSet()
        self.colorSet.set('note', curses.color_pair(1))
        self.colorSet.set('error', curses.color_pair(2))
        self.colorSet.set('message recieved', curses.color_pair(3))
        self.colorSet.set('bluetoothManager', curses.color_pair(4))
        self.colorSet.set('options', curses.color_pair(5))
    
        # Get the hight and width of the main window and ctablealculate the
        # dimentions of the display and command windows
        (maxY, maxX) = stdscr.getmaxyx()
        commandHeight = int(maxY * 0.1)
        if commandHeight < self.COMMAND_WINDOW_MIN_HEIGHT:
            commandHeight = self.COMMAND_WINDOW_MIN_HEIGHT
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
    
        # use the displayWindow class and give it dwin
        self.dis = displayWindow.DisplayWindow(dwin, \
                                               self.colorSet, \
                                               self.displayLock)
        self.disQueue = self.dis.getQueue()
        
        self.info = InfoBar(iwin, self.colorSet, self.displayLock)
        self.opt = OptionsBar(swin, self.colorSet, self.displayLock)
    
        # Put a Textbox object in the command_window
        self.tbox = threadedTextBox.ThreadedTextBox(cwin)
        
        self.dis.addEntry("Note:", 'note', "Display established!")
        
        self.btmf = bluetoothMessageFormatter.BluetoothMessageFormatter( \
                                                                dis=self.dis)
        self.btm = bluetoothManager.BluetoothManager(UUID, \
                                                     uiEvent=self.btmf.event)
        self.btmf.setQueues(self.btm.getQueues())
        self.btmf.start()
        self.btm.setStateCallback(self._bluetoothStateChange)
        self.btm.startStateCallback()
        
        self.newState = self.STATE['connect']
        return
        
    def __enterConnect(self):
        self.opt.update(getString('options_connect'))
        self.info.update(getString('info_connect_options'))
    
    def __Connect(self):
        while self.newState == self.STATE['connect']:
            #self.info.update(getString('info_connect'))
            userInput = self.__getCommand()
            logging.debug("User Input: " + str(userInput))
            
            if userInput == 'server connect':
                self.btm.connectAsServer()
            elif userInput == 'client connecct':
                #self.btm.connectAsClient(macAddress)
                pass
            elif userInput == 'exit':
                self.dis.addEntry("Note", 'note', "Good Bye.")
                self.newState = self.STATE['stop']
    
    def __leaveConnect(self):
        pass
    
    def __enterListen(self):
        self.opt.update(getString('options_listen'))
        self.info.update(getString('info_listen'))
        pass
    
    def __Listen(self):
        while self.newState == self.STATE['listen']:
            userInput = self.__getCommand()
            if userInput == 'disconnect':
                self.newState = self.STATE['disconnect']
                return
            elif userInput == 'compose':
                self.composeAddress = None
                self.newState = self.STATE['compose']
                return
            elif userInput == 'reply':
                self.composeAddress = self.lastMessageSender
                self.newState = self.STATE['compose']
                return
    
    def __leaveListen(self):
        pass    
    
    def __enterCompose(self):
        pass
    
    def __Compose(self):
        pass # TODO: Compose
    
    def __leaveCompose(self):
        pass  
    
    def __enterDisconnect(self):
        pass
    
    def __Disconnect(self):
        self.btm.stop()
        self.disconnectEvent.wait(timeout=6)
        self.disconnectEvent.clear()
    
    def __leaveDisconnect(self):
        pass
    
    def __stop(self):
        self.dis.addEntry("Note:", 'note', "Stopping...")
        self.btm.stop()
        self.btmf.stop()
        self.dis.addEntry("Note:", 'note', "Press [Space Bar] to quit!")
        self.tbox.stop()
        logging.info("ThreadedTextBox stopped")
        self.dis.stop()
        logging.info("DisplayWindow stoped")
        self.FSMBoolean = False
        
    def __getCommand(self):
        """Access point for getting a single key-combo keystroke
        
        """
        while True:
            ch = self.tbox.getInput()
            if self.state == self.STATE['start']:
                pass # No commands
            elif self.state == self.STATE['connect']:
                if ch == curses.ascii.CAN: # ^X
                    return 'exit'
                elif ch == curses.ascii.SO: # ^N
                    return 'server connect'
                elif ch == curses.ascii.NAK: # ^U
                    return 'client connect'
                elif ch == 'pass':
                    return 'pass'
            elif self.state == self.STATE['disconnect']:
                pass # No commands
            elif self.state == self.STATE['listen']:
                if ch == curses.ascii.CAN: # ^X
                    return 'disconnect'
                elif ch == curses.ascii.SI: # ^O
                    return 'compose'
                elif ch == curses.ascii.ENQ: # ^E
                    return 'reply'
            elif self.state == self.STATE['compose']:
                pass # Commands are in the threadedTextBox
            elif self.state == self.STATE['stop']:
                pass # Commands are in the threadedTextBox
            
    def _bluetoothStateChange(self, btState):
        """Callback method passed to the BluetoothManager state var.
        
        This method is run on a thread created in Handler. It is run
        every time the BluetoothManager's state variable changes. the
        state variable is passed through the parameter btState. btState
        can be any of the three options in the BluetoothManager's
        constant STATE (none, connecting, connected).
        """
        
        logging.debug("CALLBACK!")
        if self.state == self.STATE['connect']:
            if btState == self.btm.STATE['none']:
                pass # Shouldn't happen
            elif btState == self.btm.STATE['connecting']:
                logging.debug("CONNECTING")
                self.info.update(getString('info_connect_attempting'))
            elif btState == self.btm.STATE['connected']:
                logging.debug("CONNECTED")
                self.newState = self.STATE['listen']
                self.tbox.cancel() # Stop waiting for an input
                
        elif self.state == self.STATE['disconnect']:
            if btState == self.btm.STATE['none']:
                self.newState = self.STATE['connect']
                self.disconnectEvent.set()
            elif btState == self.btm.STATE['connecting']:
                pass # Shouldn't happen
            elif btState == self.btm.STATE['connected']:
                pass # Shouldn't happen
            
        elif self.state == self.STATE['listen']:
            if btState == self.btm.STATE['none']:
                logging.debug("NONE")
                self.newState = self.STATE['connect']
                self.tbox.cancel()
            elif btState == self.btm.STATE['connecting']:
                pass # Shouldn't happen
            elif btState == self.btm.STATE['connected']:
                pass # Shouldn't happen
            
        elif self.state == self.STATE['compose']:
            if btState == self.btm.STATE['none']:
                pass # TODO: Compose
            elif btState == self.btm.STATE['connecting']:
                pass # Shouldn't happen
            elif btState == self.btm.STATE['connected']:
                pass # Shouldn't happen
        
class OptionsBar():
    def __init__(self, win, colorSet, displayLock):
        self.win = win
        self.win.leaveok(True)
        self.colorSet = colorSet
        self.win.bkgd(' ', self.colorSet.g('options'))
        self.win.refresh()
        self.displayLock = displayLock
        
    def update(self, text):
        self.displayLock.acquire()
        self.win.attron(self.colorSet.g('options'))
        self.win.erase()
        self.win.addstr(text)
        self.win.attroff(self.colorSet.g('options'))
        self.win.refresh()
        self.displayLock.release()
        
class InfoBar():
    def __init__(self, win, colorSet, displayLock):
        self.win = win
        self.win.leaveok(True)
        self.colorSet = colorSet
        self.displayLock = displayLock
        
    def update(self, text):
        self.displayLock.acquire()
        self.win.erase()
        self.win.addstr(text)
        self.win.refresh()
        self.displayLock.release()
        
def startUI():
    ui = UI()
    curses.wrapper(ui.main)
            
        
        
        