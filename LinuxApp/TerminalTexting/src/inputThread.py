'''
Created on Feb 25, 2019

@author: jj
'''
from threading import Thread, Event

class InputThread(Thread):
    '''
    classdocs
    '''
    
    KEYBOARD_INPUT = "keyboardInput"

    def __init__(self, outputQueue, tbox):
        '''
        Constructor
        '''
        super(InputThread, self).__init__()
        self.output = outputQueue
        self.tbox = tbox
        self.running = True
        self.myEvent = Event()
        self.myEvent.set()
        self.start()
        
    def join(self, timeout=None):
        self.running = False
        Thread.join(self, timeout=timeout)
        
    def run(self):
        while self.running:
            ch = self.tbox.getInput()
            if self.running and self.myEvent.isSet():
                self.output.put((self.KEYBOARD_INPUT, ch))
            self.myEvent.wait()
                
    def suspend(self):
        self.myEvent.clear()
        
    def resume(self):
        self.myEvent.set()