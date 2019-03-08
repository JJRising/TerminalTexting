'''
Created on Feb 25, 2019

@author: jj
'''
from src.bluetoothService import BluetoothService
import logging

class BluetoothManager(BluetoothService):
    '''Extended BluetoothService for project specific use
    
    Overrides the _outputBluetoothMessage so that the message can be
    formatted into the displayThreads required form.
    '''
    
    # Message Types
    __TEXT_MESSAGE = 255
    __SPECIAL = 0
    
    # Output Types
    OUTPUT_RECEIVED_TEXT_MESSAGE = "receivedText"

    def __init__(self, uuid, serviceName, outputQueue):
        super(BluetoothManager, self).__init__(uuid, \
                                               serviceName, \
                                               outputQueue)
    
    def _outputBluetoothMessage(self, buffer):
        messageType = buffer[0]
        if messageType == self.__TEXT_MESSAGE:
            # recieved text message
            self.outputQueue.put((self.OUTPUT_RECEIVED_TEXT_MESSAGE, \
                                  {'message': TextMessage(buffer[1:])}))
        elif messageType == self.__SPECIAL:
            # Special instruction
            pass
        else:
            # Something went wrong
            pass
        
class MessageBuffer():
    def __init__(self, byteArray):
        self.pointer = 0
        self.buffer = byteArray
        
    def read(self, num):
        newPointer = self.pointer + num
        output = self.buffer[self.pointer : newPointer]
        self.pointer = newPointer
        if len(output) == 1:
            return output[0]
        else:
            return output
        
    
class TextMessage():
    """Contains phoneNumber, contactName, and message as Strings"""
    def __init__(self, byteArray):
        logging.debug(f"byteArray: {byteArray}")
        msg = MessageBuffer(byteArray)
        # get the phone Number
        self.phoneNumber = msg.read(12).decode()
        # get the contact's Name
        contactLength = int(msg.read(1))
        self.contactName = msg.read(contactLength).decode()
        # get the message
        messageLengthArray = msg.read(4)
        messageLength = int.from_bytes(messageLengthArray, \
                                       'big', \
                                       signed=True)
        self.message = msg.read(messageLength).decode()
        logging.debug(f"phoneNumber: {self.phoneNumber}")
        logging.debug(f"contactLength: {contactLength}")
        logging.debug(f"contactName: {self.contactName}")
        logging.debug(f"messageLength: {messageLength}")
        logging.debug(f"message: {self.message}")
        
def getBytes(phoneNumber, message):
    output = phoneNumber.encode()
    output += b'\x04'
    output += b'none'
    mLength = int(len(message))
    output += mLength.to_bytes(4, 'big', signed=True)
    output += message.encode()
    return output
    
        
        
