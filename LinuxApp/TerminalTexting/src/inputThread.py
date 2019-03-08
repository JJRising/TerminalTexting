'''
@author: jj
'''
from threading import Thread
from curses import ascii

class InputThread(Thread):
    '''Thread class specifically for collecting keystokes
    
    Has two modes. In Standard Mode, keystokes are collected and passed
    to the outputQueue. When switching to edit mode, a displayThread is
    passed and the keystokes or commands are passed there using the 
    displayThread's tBoxCommand(ch) method call.
    '''
    
    KEYBOARD_INPUT = "keyboardInput"
    OUTPUT_GATHER = "gather"
    OUTPUT_CANCEL = "cancel"
    
    __STANDARD_MODE = "standard"
    __EDIT_MODE = "edit"

    def __init__(self, outputQueue, tbox):
        super(InputThread, self).__init__()
        self.output = outputQueue
        self.tbox = tbox
        self.running = True
        self.mode = self.__STANDARD_MODE
        self.displayThread = None
        self.start()
    
    def editMode(self, value=True, displayThread=None):
        """Change the input mode between standard and edit
        
        If the value is set to False, the display thread may be left as
        None. If the value is left to be Ture, a displayThread must be
        provided.
        
        value - Boolean where true sets the input thread to edit mode
        displayThread - pointer to a displayThread.
        """
        if value:
            self.mode = self.__EDIT_MODE
        else:
            self.mode = self.__STANDARD_MODE
        self.displayThread = displayThread
        
    def join(self, timeout=None):
        """terminates and joins the thread after 1 last keystroke"""
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
            
            
            
            
            
            