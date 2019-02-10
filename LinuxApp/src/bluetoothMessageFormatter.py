'''
Created on Jan 31, 2019

@author: jj
'''

from threading import Thread, Event

class BluetoothMessageFormatter():
    '''
    classdocs
    '''


    def __init__(self, uiQueue=None, messageQueue=None, dis=None):
        '''
        Constructor
        '''
        self.event = Event()
        self.uiQueue = uiQueue
        self.messageQueue = messageQueue
        self.dis = dis
        self.running = True
        self.myThread = Thread(target=self.run)
        
    def run(self):
        while self.running:
            self.event.wait()
            self.event.clear()
            while not self.uiQueue.empty():
                message = self.uiQueue.get()
                self.dis.addEntry("BluetoothManager:", \
                                  'bluetoothManager', \
                                  message)
            while not self.messageQueue.empty():
                message = self.messageQueue.get()
                # TODO: Add formatting
                self.dis.addEntry("Text Message:", \
                                   'message recieved', \
                                   message)
                
    def start(self):
        self.myThread.start()
        
    def stop(self):
        self.running = False
        self.event.set()
        self.myThread.join()
        
    def setQueues(self, lt):
        self.messageQueue = lt[0]
        self.uiQueue = lt[1]
        
        
        
        