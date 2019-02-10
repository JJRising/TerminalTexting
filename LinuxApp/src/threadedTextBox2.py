'''
Created on Jan 26, 2019

@author: jj
'''

import curses.textpad
import logging
import threading
from src.constants import STATE
from queue import Queue

class ThreadedTextBox(curses.textpad.Textbox):
    '''Extention of a curses Textbox that runs on a dedicated thread.
    
    A seperate thread is created upon construction that is listening
    for user input. This textbox should be used in situations where it
    is the only point of user input in the application.
    
    Public Methods:
        getInput()
        getMessage()
        stop()
    '''

    def __init__(self, context, win):
        curses.textpad.Textbox.__init__(self, win)
        self.m = context
        self.__running = True
        self.__myQueue = Queue()
        self.__QuFlag = threading.Event()
        self.__myThread = threading.Thread(target=self.__run)
        self.__myThread.start()
        
    
    def __gather(self):
        ret = curses.textpad.Textbox.gather(self)
        ret = ret.replace("\n", "")
        ret = ret.strip(" ")
        return ret
        
    def __do_command(self, ch):
        if self.m.state == STATE['start']:
            pass # no commands
        
        elif self.m.state == STATE['connect']:
            if ch == curses.ascii.CAN: # ^X
                return 'exit'
            elif ch == curses.ascii.SO: # ^N
                return 'server connect'
            elif ch == curses.ascii.NAK: # ^U
                return 'client connect'
            
        elif self.m.state == STATE['disconnect']:
            pass # no commmands
        
        elif self.m.state == STATE['listen']:
            if ch == curses.ascii.CAN: # ^X
                return 'disconnect'
            elif ch == curses.ascii.SI: # ^O
                return 'compose'
            elif ch == curses.ascii.ENQ: # ^E
                return 'reply'
            
        elif self.m.state == STATE['compose']:
            self._update_max_yx()
            (y, x) = self.win.getyx()
            self.lastcmd = ch
            if curses.ascii.isprint(ch):
                if y < self.maxy or x < self.maxx:
                    self._insert_printable_char(ch)
            elif ch in (curses.ascii.STX,curses.KEY_LEFT, curses.ascii.BS,curses.KEY_BACKSPACE):
                if x > 0:
                    self.win.move(y, x-1)
                elif y == 0:
                    pass
                elif self.stripspaces:
                    self.win.move(y-1, self._end_of_line(y-1))
                else:
                    self.win.move(y-1, self.maxx)
                if ch in (curses.ascii.BS, curses.KEY_BACKSPACE):
                    self.win.delch()
            elif ch == curses.KEY_RIGHT:
                if x < self.maxx:
                    self.win.move(y, x+1)
                elif y == self.maxy:
                    pass
                else:
                    self.win.move(y+1, 0)
            elif ch == curses.KEY_DOWN:
                if y < self.maxy:
                    self.win.move(y+1, x)
                    if x > self._end_of_line(y+1):
                        self.win.move(y+1, self._end_of_line(y+1))
            elif ch == curses.KEY_UP:
                if y > 0:
                    self.win.move(y-1, x)
                    if x > self._end_of_line(y-1):
                        self.win.move(y-1, self._end_of_line(y-1))
            elif ch == curses.ascii.ENQ: # ^E
                return 'cancel'
            elif ch == curses.ascii.VT: # ^K
                return 'send'
            
        elif self.m.state == STATE['stop']:
            return True # no commands
        
        self.win.refresh()
        return None
    
    def __getUserInput(self):
        while True:
            ch = self.win.getch()
            ret = self.__do_command(ch)
            if ret:
                break
        return ret
    
    def __run(self):
        logging.info("ThreadedTextBox running")
        while self.__running:
            ret = [self.__getUserInput(), self.__gather()]
            self.__myQueue.put(ret)
            self.__QuFlag.set()
    
    def stop(self):
        self.__running = False
        self.__myThread.join()
    
    def waitFor(self):
        self.__QuFlag.wait()
        
    def resetFlag(self):
        if self.__myQueue.empty():
            self.__QuFlag.clear()
        
    def getInput(self):
        self.waitFor()
        ret = self.__myQueue.get()
        self.resetFlag()
        return ret[0]
    
    def getMessage(self):
        self.waitFor()
        ret = self.__myQueue.get()
        self.resetFlag()
        return ret
        
    def isSet(self):
        return self.__QuFlag.is_set()
        
        
        
        
        
        