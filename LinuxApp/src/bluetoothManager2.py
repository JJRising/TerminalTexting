'''
Created on Jan 15, 2019

@author: jj

'''

import threading
import bluetooth
import src.pairDevices
from src.Handler import StateHandler
import logging
    
# Constants
_UUID = "56abddf0-d4d2-45c7-9b2b-7837582d436f"
_UI_MESSAGE_TYPE = ["note", "error"]

class BluetoothManager():    
    STATE = {'none': "None", \
          'connecting': "Connecting", \
          'connected': "Connected"}
    
    def __init__(self, uiQueue=None, uiEvent=None):
        self.__state = StateHandler()
        self.__CThread = None
        self.__LThread = None
        self.__server_sock = None
        self.__client_sock = None
        self.__client_info = None
        self.__uiQueue = uiQueue
        self.__uiEvent = uiEvent
          
    def isConnected(self):
        """Return True if there is a current connection"""
        
        return self.__state.get() == self.STATE['connected']
    
    def who(self):
        """Return the name and MAC_ADDRESS of the connection"""
        
        if self.__client_info == None:
            return ("No Connection", "")
        else:
            return self.__client_info
    
    def connectAsServer(self):
        """Attempt to make a connection as a server"""
        
        if self.__state.get() == self.STATE['none']:
            self.__state.update(self.STATE['connecting'])
            self.__CThread = threading.Thread( \
                                        target=self._connectAsServerThread)
            self.__CThread.start()
            return self.__CThread
    
    def _connectAsServerThread(self):
        """Internal method to make connection using pyBluez"""
        
        logging.info("BluetoothManager - Attempting to find connection")
        try:
            self.__server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.__server_sock.bind(("", bluetooth.PORT_ANY))
            self.__server_sock.listen(1)
        except Exception as e:
            logging.error("BluetoothManager - Failed to establish server " \
                          "socket: ", \
                          e)
            self.__errorUI("Failed to establish server socket")
            self.__state.update(self.STATE['none'])
            return
        
        logging.info("BluetoothManager - Server sockets created")
        
        try:
            bluetooth.advertise_service(self.__server_sock, \
                    "DesktopTexting", \
                    service_id = _UUID, \
                    service_classes = [_UUID, bluetooth.SERIAL_PORT_CLASS], \
                    profiles = [bluetooth.SERIAL_PORT_PROFILE])
        except Exception as e:
            logging.error("BluetoothManager - Error in advertise service: ", \
                          e)
            self.errorUI("Error in advertise service")
            self.__state.update(self.STATE['none'])
            return
        
        self.__noteUI("Awaiting connection...")
        logging.info("BluetoothManager - advertising the service")
        
        try:
            self.__client_sock, self.__client_info = \
                                        self.__server_sock.accept()
        except Exception as e:
            logging.error("BluetoothManager - Failed to accept connection: ", \
                          e)
            self.errorUI("Failed to accept connection")
            self.__state.update(self.STATE['none'])
            return
        
        self.__noteUI("Accepted connection from " + str(self.__client_info))
        logging.info("BluetoothManager - Accepted connection from: " \
                     + str(self.__client_info))
        
        self.__state.update(self.STATE['connected'])
        
    '''
     ' Used to create a new listenThread.
    '''
    def listen(self):
        assert self.__state.get() == self.STATE['connected'], \
                                    "Trying to listen when not connected!"
                                    
        self.__LThread = threading.Thread(target=self._listenThread)
        self.__LThread.start()
        return self.__LThread
        
    '''
     ' A thread that will listen for incoming messages from the connected
     ' bluetooth device. Should be called using the 'listen()' method.
    '''
    def _listenThread(self):
        logging.info("BluetoothManager - Listening for messages")
        while self.__state.get() == self.STATE['connected']:
            try:
                buffer = self.__client_sock.recv(1024)
                self.__recievedMessage(buffer)
                logging.info("BluetoothManager - Recieved message from " \
                             "connection")
            except IOError:
                self.__connectionLost()
                return
            
        
    def __connectionLost(self):
        logging.error("BluetoothManager - Connection lost")
        self.__state.update(self.STATE['none'])
        self.__errorUI("Lost connection")
    
    '''
     ' Stop all currently running bluetooth threads and close any existing
     ' server and client sockets
    '''
    def stop(self):
        logging.info("BluetoothManager - Bluetooth Manager stopping")
        '''
        assert self.__state != self.STATE['none'], \
                                "No current connections or attemps"
                                '''
        # set the self.STATE to be none
        self.__state.update(self.STATE['none'])
            
        # Close any existing sockets
        if self.__client_sock != None:
            try:
                self.__client_sock.close()
                logging.info("BluetoothManager - client socket closed")
            except:
                self.errorUI("Could not close client socket")
        if self.__server_sock != None:
            #self.__server_sock.setblocking(False)
            try:
                self.__server_sock.close()
                logging.info("BluetoothManager - erver socket closed")
            except:
                self.errorUI("Could not close server socket")
        logging.info("BluetoothManager - Bluetooth Manager stoped")
        
    '''
     ' Sends a byte[] buffer to the connected bluetooth device.
    '''
    def write(self, buffer):
        assert self.__state.get() == self.STATE['connected'], \
                                    "Trying to write when not connected!"
        wThread = threading.Thread(target=self.__writeThread, args=(buffer))
        wThread.start()
        return wThread
            
    def __writeThread(self, buffer):                              
        try:
            self.cSocket.send(buffer)
            self.__noteUI("Message Sent")
            logging.info("BluetoothManager - Sent message: ", buffer)
        except IOError:
            self.__errorUI("Failed to send message")
            logging.info("BluetoothManager - Failed to send message: ", \
                         buffer)
            
    '''
     ' Methods for updating the UI for activity going on in the bluetooth
     ' module. It is up to the UI to manage pulling messages from the queue.
    '''
    def __noteUI(self, info):
        self.__uiQueue.put(['note', info])
        self.__uiEvent.set()
        
    def __errorUI(self, info):
        self.__uiQueue.put(['error', info])
        self.__uiEvent.set()
        
    def __recievedMessage(self, message):
        self.__uiQueue.put(['message recieved', message])
        self.__uiEvent.set()
    
    def setUIQueue(self, qu, event):
        self.__uiQueue = qu
        self.__uiEvent = event

'''
 ' Is used to abstract away the pairing process as it is dependent on the 
 ' operating system and bluetooth interfaces used.
'''
def pair(macAddress):
    src.pairDevices.pair(macAddress)




    
