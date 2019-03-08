'''
@author: jj
'''
from threading import Thread
from queue import Queue

class DisplayThread(Thread):
    '''Thread class specifically for outputting to the curses windows
    
    Curses is not thread safe and tends to behave poorly when multiple
    threads attempt to output to the display simotaniously. This thread
    collects output requests through a queue to handle them safely.
    '''

    __PRINT_OPTIONS = "options"
    __PRINT_STATUS = "status"
    __PRINT_TO_DISPLAY = "display"
    __TBOX_COMMAND = "tboxCommand"
    __TBOX_CLEAR = "tboxClear"
    __STOP = "stop"

    def __init__(self, dis, info, tbox, opt):
        """Constuctor
        
        dis - scollWindow
        info - textBar
        tbox - tbox
        opt - textBar
        """
        super(DisplayThread, self).__init__()
        self.dis = dis
        self.info = info
        self.tbox = tbox
        self.opt = opt
        self.input = Queue()
        self.start()
        
    def printOptions(self, text):
        self.input.put((self.__PRINT_OPTIONS, text))
        
    def printStatus(self, text):
        self.input.put((self.__PRINT_STATUS, text))
        
    def printToDisplay(self, title, titleColor, text):
        self.input.put((self.__PRINT_TO_DISPLAY, title, titleColor, text))
        
    def tBoxCommand(self, command):
        """Print characters or move cursor actions"""
        self.input.put((self.__TBOX_COMMAND, command))
        
    def clearTBox(self):
        self.input.put((self.__TBOX_CLEAR,))
        
    def join(self, timeout=None):
        self.input.put((self.__STOP,))
        Thread.join(self, timeout=timeout)
        
    def run(self):
        while True:
            command = self.input.get()
            if command[0] == self.__PRINT_OPTIONS:
                self.opt.update(command[1])
            elif command[0] == self.__PRINT_STATUS:
                self.info.update(command[1])
            elif command[0] == self.__PRINT_TO_DISPLAY:
                self.dis.addEntry(command[1], command[2], command[3])
            elif command[0] == self.__TBOX_COMMAND:
                self.tbox.do_command(command[1])
            elif command[0] == self.__TBOX_CLEAR:
                self.tbox.clear()
            elif command[0] == self.__STOP:
                break
        
        
        
        
        
        