'''
Created on Feb 20, 2019

@author: jj

# TODO: Disconnect curently does not successfully close the
        the sockets. This may likely be an issue with pybluez.
'''

from threading import Thread
from queue import Queue
import bluetooth
import logging

class BluetoothService(Thread):
    '''
    classdocs
    '''
    
    # State constants
    STATE_NONE = "none"
    STATE_CONNECTING = "connecting"
    STATE_CONNECTED = "connected"
    
    # Output Types
    OUTPUT_DISCOVER_STARTED = "discoverStarted"
    OUTPUT_DISCOVER_RESULT = "discoverResult"
    OUTPUT_DISCOVER_COMPLETE = "discoverComplete"
    OUTPUT_CONNECTION_MADE = "connectionMade"
    OUTPUT_CONNECTION_FAILED = "connectionFailedError"
    OUTPUT_CONNECTION_LOST = "connectionLostError"
    OUTPUT_DISCONNECTED = "disconnected"
    OUTPUT_BLUETOOTH_MESSAGE = "message"
    OUTPUT_WRITE_SUCCESS = "writeSuccess"
    OUTPUT_WRITE_FAILED = "writeFailed"
    OUTPUT_ERROR = "error"
    OUTPUT_NOTE = "note"
    
    # commands
    __DISCOVER = "discover"
    __SERVER_CONNECT = "serverConnect"
    __CLIENT_CONNECT = "clientConnect"
    __WRITE = "write"
    __THREAD_DONE = "done"
    __DISCONNECT = "disconnect"
    __STOP = "stop"
    
    # Thread Types
    __MAIN_THREAD = "main"
    __DISCOVERY_THREAD = "discovery"
    __CONNECTION_THREAD = "connection"
    __WRITE_THREAD = "write"

    def __init__(self, uuid, serviceName, outputQueue):
        '''Constructor
        
        The uuid and serviceName are strings and should match for 
        whatever other device you are connecting to. The outputQueue
        should be a standard Queue object that gets populated with the
        output of the service threads.
        '''
        super(BluetoothService, self).__init__()
        self.state = self.STATE_NONE
        self.uuid = uuid
        self.name = serviceName
        self.commandInput = Queue()
        self.outputQueue = outputQueue
        self.threadList = []
        self._mySock = None
        self._remoteSock = None
        self._remoteInfo = None
        self._messageCounter = 0
        self.canceled = False
        self.start()
        
    def discover(self):
        self.commandInput.put((self.__DISCOVER,))
        
    def connectAsServer(self):
        if self.state == self.STATE_NONE:
            self.commandInput.put((self.__SERVER_CONNECT,))
        else:
            raise BluetoothManagerError()
    
    def connectAsClient(self, macID):
        if self.state == self.STATE_NONE:
            self.commandInput.put((self.__Client_CONNECT, macID))
        else:
            raise BluetoothManagerError()
    
    def write(self, message):
        if self.state == self.STATE_CONNECTED:
            self._messageCounter += 1
            messageID = self._messageCounter
            self.commandInput.put((self.__WRITE, message, messageID))
            return messageID
        else:
            raise BluetoothWriteError()
        
    def disconnect(self):
        if self.state != self.STATE_NONE:
            logging.debug("Sending disconnect input command")
            self.commandInput.put((self.__DISCONNECT,))
        
    def join(self, timeout=None):
        self.commandInput.put((self.__STOP,))
        Thread.join(self, timeout=timeout)
    
    def _output(self, outType, args):
        self.outputQueue.put((outType, args))
        
    def _outputDiscoveryStarted(self):
        self._output(self.OUTPUT_DISCOVER_STARTED, {})
        
    def _outputDiscoveryResult(self, result):
        self._output(self.OUTPUT_DISCOVER_RESULT, {'result': result})
        
    def _outputDiscoveryComplete(self):
        self._output(self.OUTPUT_DISCOVER_COMPLETE, {})
        
    def _outputConnectionMade(self, device):
        self._output(self.OUTPUT_CONNECTION_MADE, {'device': device})
        
    def _outputConnectionFailed(self, e, comment):
        self._output(self.OUTPUT_CONNECTION_FAILED, {'comment': comment, \
                                                     'error': e})
        
    def _outputConnectionLost(self, e, comment):
        self._output(self.OUTPUT_CONNECTION_LOST, {'comment': comment, \
                                                   'error': e})
        
    def _outputDisconnected(self, comment):
        self._output(self.OUTPUT_DISCONNECTED, {'comment': comment})
        
    def _outputWriteSuccess(self, messageID):
        self._output(self.OUTPUT_WRITE_SUCCESS, {'messageID': messageID})
        
    def _outputWriteFailed(self, messageID, e, comment):
        self._output(self.OUTPUT_WRITE_FAILED, {'messageID': messageID, \
                                                'comment': comment, \
                                                'error': e})

    def _outputBluetoothMessage(self, buffer):
        self._output(self.OUTPUT_BLUETOOTH_MESSAGE, {'message': buffer})
        
    def _outputError(self, e, comment):
        self._output(self.OUTPUT_ERROR, {'comment': comment, 'error': e})
    
    def _outputNote(self, note):
        self._output(self.OUTPUT_NOTE, {'note': note})
    
    #-----------------------------Internal Methods-----------------------------
    
    def _threadDone(self, myThread):
        self.commandInput.put((self.__THREAD_DONE, myThread))
    
    def run(self):
        while True:
            logging.debug(f"BluetoothService trying to get a command")
            command = self.commandInput.get()
            logging.info(f"BluetoothService command: {command[0]}")
            if command[0] == self.__DISCOVER:
                newThread = WorkerThread(self, target=self._discoverTread)
                self.threadList.append((self.__DISCOVERY_THREAD, newThread))
                newThread.start()
                continue
                
            elif command[0] == self.__SERVER_CONNECT:
                newThread = WorkerThread(self, 
                                         target=self._connectAsServerThread)
                self.threadList.append((self.__CONNECTION_THREAD, newThread))
                newThread.start()
                logging.debug("IS THIS BLOCKING???")
                continue
                
            elif command[0] == self.__CLIENT_CONNECT:
                newThread = WorkerThread(self, 
                                         target=self._connectAsClientThread,
                                         args=(command[1],))
                self.threadList.append((self.__CONNECTION_THREAD, newThread))
                newThread.start()
                continue
            
            elif command[0] == self.__WRITE:
                newThread = WorkerThread(self,
                                         target=self._writeThread,
                                         args=(command[1], command[2]))
                self.threadList.append((self.__WRITE_THREAD, newThread))
                newThread.start()
                continue
            
            elif command[0] == self.__THREAD_DONE:
                myThread = command[1]
                try:
                    myThread.join(4)
                except TimeoutError:
                    pass
                for el in self.threadList:
                    if el[1] == myThread:
                        self.threadList.remove(el)
                        break
                continue
                
            elif command[0] in (self.__DISCONNECT, self.__STOP):
                logging.debug("disconnecting, hi")
                self.canceled = True
                if self._remoteSock != None:
                    try:
                        self._remoteSock.close()
                        logging.debug("Remote Sock closed")
                    except Exception as e:
                        self._outputError(e, "Failed to close remote socket")
                    self._remoteSock = None
                    self._remoteInfo = None
                if self._mySock != None:
                    try:
                        self._mySock.close()
                        logging.debug("My Sock closed")
                    except Exception as e:
                        self._outputError(e, "Failed to close socket")
                    self._mySock = None
                while len(self.threadList) > 0:
                    trd = self.threadList.pop(-1)
                    trd[1].cancel()
                    trd[1].join()
                self.state = self.STATE_NONE
                self.canceled = False
                logging.debug("Should be disconnected now")
                if command[0] == self.__STOP:
                    return
                else:
                    continue
        
    def _discoverTread(self):
        self._outputDiscoveryStarted()
        devices = bluetooth.discover_devices(duration=8, 
                                             flush_cache=True, 
                                             lookup_names=True, 
                                             lookup_class=False, 
                                             device_id=-1)
        self._outputDiscoveryResult(devices)
        self._outputDiscoveryComplete()
        
    def _connectAsServerThread(self):
        try:
            self._mySock = bluetooth.BluetoothSocket()
            self._mySock.bind(("", bluetooth.PORT_ANY))
            self._mySock.listen(1)
        except Exception as e:
            self._connectionFailed(e, "Failed to create a server socket.")
            return
            
        if (self.canceled):
            self._connectionCanceled()
            return 
        self._outputNote("Successfully obtained a socket: " \
                         + str(self._mySock))
        
        try:
            bluetooth.advertise_service( \
                sock=self._mySock, \
                name=self.name, \
                service_id=self.uuid, \
                service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS], \
                profiles=[bluetooth.SERIAL_PORT_PROFILE] \
                )
        except Exception as e:
            self._connectionFailed(e, "Failed to advertise the service.")
            return
        
        if (self.canceled):
            self._connectionCanceled()
            return 
        self._outputNote("Awaiting connection")
        
        try:
            self._remoteSock, self._remoteInfo = self._mySock.accept()
        except Exception as e:
            self._connectionFailed(e, "There was an issue accepting " \
                                      "connections.")
            return
            
        if (self.canceled):
            self._connectionCanceled()
            return
        self._connectionMade()
        self._listen()
    
    def _connectAsClientThread(self, address):
        try:
            foundServices = bluetooth.find_service(self.name, \
                                                   self.uuid, \
                                                   address)
        except Exception as e:
            self._connectionFailed(e, "Could not search for any matching " \
                                      "broadcasts.")
            
        
        if (self.canceled):
            self._connectionCanceled()
            return 
        if len(foundServices) == 0:
            self._connectionFailed(None, "Didn't find any matching broadcasts")
            
        match = foundServices[0]
        self._remoteInfo = (match['host'], match['port'])
        self._remoteSock = bluetooth.BluetoothSocket()
        try:
            self._remoteSock.connect()
        except Exception as e:
            self._connectionFailed(e, "Error when connection to the remote " \
                                      "Device.")
        
        
        if (self.canceled):
            self._connectionCanceled()
            return 
        self._connectionMade()
        self._listen()
            
    def _connectionMade(self):
        device = RemoteDevice(None, self._remoteInfo[0], self._remoteInfo[1])
        self._outputConnectionMade(device)
        self.state = self.STATE_CONNECTED
    
    def _connectionFailed(self, e, reason):
        self._outputConnectionFailed(e, reason)
        self.state = self.STATE_NONE
        
    def _connectionCanceled(self):
        self._outputNote("Stopping connection.")
        self.state = self.STATE_NONE
    
    def _connectionLost(self, e):
        self._outputConnectionLost(e, "The connection was lost")
        self.state = self.STATE_NONE
    
    def _listen(self):
        while self.state == self.STATE_CONNECTED:
            try:
                buffer = self._remoteSock.recv(1024)
                logging.info(f"RecievedBluetoothMessage: {buffer}")
                self._outputBluetoothMessage(buffer)
            except IOError as e:
                logging.debug("IOError in listen")
                if not self.canceled:
                    self._connectionLost(e)
                else:
                    self._outputDisconnected("Disconnected")
                return
    
    def _writeThread(self, buffer, messageID):
        try:
            logging.debug(f"Sending: {buffer}")
            self._remoteSock.send(buffer)
        except IOError as e:
            self._outputWriteFailed(messageID, e, "")
        else:
            self._outputWriteSuccess(messageID)
        
class WorkerThread(Thread):
    def __init__(self, context, group=None, target=None, name=None, args=(), 
                 kwargs={}, *, daemon=None):
        self.context = context
        self.canceled = False
        super(WorkerThread, self).__init__(group=group, \
                                           target=target, \
                                           name=name, \
                                           args=args, \
                                           kwargs=kwargs, \
                                           daemon=daemon)
        
    def run(self):
        Thread.run(self)
        self.context._threadDone(self);
        
    def cancel(self):
        self.canceled = True
        
class RemoteDevice:
    def __init__(self, name, address, channel):
        self.name = name
        self.address = address
        self.channel = channel
        
class BluetoothManagerError(Exception):
    """Generic Exception raised for issue with the manager"""  
    pass      
    
class BluetoothWriteError(Exception):
    """Exception raised when trying to write without a connection"""
    pass
        
        
    