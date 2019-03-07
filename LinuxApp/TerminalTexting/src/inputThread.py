'''
Created on Feb 25, 2019

@author: jj
'''
from threading import Thread
from curses import ascii

class InputThread(Thread):
    '''
    classdocs
    '''
    
    KEYBOARD_INPUT = "keyboardInput"
    OUTPUT_GATHER = "gather"
    OUTPUT_CANCEL = "cancel"
    
    __STANDARD_MODE = "standard"
    __EDIT_MODE = "edit"

    def __init__(self, outputQueue, tbox):
        '''
        Constructor
        '''
        super(InputThread, self).__init__()
        self.output = outputQueue
        self.tbox = tbox
        self.running = True
        self.mode = self.__STANDARD_MODE
        self.displayThread = None
        self.start()
    
    def editMode(self, value=True, displayThread=None):
        if value:
            self.mode = self.__EDIT_MODE
        else:
            self.mode = self.__STANDARD_MODE
        self.displayThread = displayThread
        
    def join(self, timeout=None):
        self.running = False
        Thread.join(self, timeout=timeout)
        
    def run(self):
        while self.running:
            ch = self.tbox.getInput()
            if self.mode == self.__STANDARD_MODE:
                if self.running:
                    self.output.put((self.KEYBOARD_INPUT, ch))
            else: # Edit Mode
                if self.running:
                    if ch == ascii.VT:
                        # gather
                        self.output.put((self.OUTPUT_GATHER, \
                                         {'message': self.tbox.gather()}))
                    elif ch == ascii.ENQ:
                        # cancel
                        self.output.put((self.OUTPUT_CANCEL, ()))
                    else:
                        # send to display thread
                        self.displayThread.tBoxCommand(ch)
            
            
            
            
            
            