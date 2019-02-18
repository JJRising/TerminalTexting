'''
Created on Jan 31, 2019

@author: jj
'''

from threading import Thread, Event
import logging

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
                buffer = self.messageQueue.get()
                number = buffer[0:12]
                contactLength = int(buffer[12])
                contact = buffer[13: 13 + contactLength]
                messageLengthArray = buffer[13 + contactLength : \
                                            13 + contactLength + 4]
                messageLength = messageLengthArray[0] \
                                + messageLengthArray[1]*128 \
                                + messageLengthArray[2]*128*128 \
                                + messageLengthArray[3]*128*128*128
                message = buffer[13 + contactLength + 4 : \
                                 13 + contactLength + 4 + messageLength]
                logging.debug(messageLength)
                logging.debug(message)
                # TODO: Add formatting
                self.dis.addEntry("Text Message from " + str(contact) + ": ", \
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
        
        
        
        