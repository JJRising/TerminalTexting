'''
Created on Jan 15, 2019

@author: jj

'''

from src.handler import Handler
from queue import Queue
from threading import Thread, Event
import bluetooth
import logging


class BluetoothManager():
    """Create and manage bluetooth connections.
    
    Class deigning to asyncronusly manage bluetooth connections. This
    class utilizes the pyBluez project to interact with the bluetooth
    adapter. Results are returned through a Queue that should be
    obtained along with it's event using that accessor
    'getMessageQueueEvent()'. 
    
    Public Constants:
        STATE
        WRITE_SENT
        WRITE_FAILED
    
    Public Methods:
        connectAsServer() - Entry Point (1 of 2)
        connectAsClient() - Entry Point (1 of 2)
        isConnected()
        who()
        write()
        stop()
        setStateCallback()
        startStateCallback()
        stopStateCallback()
        getUIQueueEvent()
        getMessageQueueEvent()
    """
    
    
    STATE = {'none': "None", \
          'connecting': "Connecting", \
          'connected': "Connected"}
    WRITE_SENT = "Message Sent"
    WRITE_FAILED = "Message Failed"
    
    __SUCCESS = 'Success'
    __FAILURE = "Failure"
    
    
    def __init__(self, uuid, uiEvent=None):
        self.uuid = uuid
        self._state = Handler(self.STATE['none'])
        self._mySock = None            # Socket for this device
        self._remoteSock = None        # Socket for the remote device
        self._remoteInfo = None
        self._messageQueue = Queue()
        self._uiQueue = Queue()
        if uiEvent == None:
            self._messageEvent = Event()
            self._uiEvent = Event()
        else:
            self._messageEvent = uiEvent
            self._uiEvent = uiEvent
        # Thread related variables
        self.__connectionThread = None
        self.__running = False
        self._uiMessage("BluetoothManager established!")
    
    def connectAsServer(self):
        """Entry Point (1/2). Attempt to allow connection as a server.
        
        Forks a new connection thread passing 'Server' along as an 
        argument'
        """
        if self._state.get() == self.STATE['none']:
            self.__running = True
            self._state.update(self.STATE['connecting'])
            self.__connectionThread = \
                            Thread(target=self.__run, args=("Server",))
            self.__connectionThread.start()
    
    def connectAsClient(self, macAddress):
        """Entry Point (1/2). Attempt to make connection as a client.
        
        Forks a new connection thread passing the macAddress along as
        an argument'
        """
        if self._state.get() == self.STATE['none']:
            self._state.update(self.STATE['connecting'])
            self.__running = True
            self.__connectionThread = \
                            Thread(target=self.__run, args=(macAddress,))
            self.__connectionThread.start()
          
    def isConnected(self):
        """Return True if there is a current connection"""
        return self._state.get() == self.STATE['connected']
    
    def who(self):
        """Return the name and MAC_ADDRESS of the connection"""
        return self._remoteInfo
    
    def write(self, buffer, sync=True):
        """Fork a thread to send 'buffer' as byte data to a connection.
        
        Checks to make sure that there is a currently managed
        connection to a remote device. Throws a BluetoothManagerError
        if one isnt available. If one is this method will fork a thread
        that will convert the data in buffer into a sendable byte[] and
        will attempt to send it to the connected device.
        
        This method will return the forked thread if sync is set to
        True. Otherwise it will attempt to join the forked thread.
        """
        # Check to see if there is a connection
        if self._state.get() != self.STATE['connected']:
            raise BluetoothWriteError()
        myThread = Thread(target=self.__writeThread(), args=(buffer,))
        myThread.start()
        if sync:
            try:
                myThread.join()
            except Exception:
                raise BluetoothManagerError("Threading Error. Unable to " \
                                            " join write Thread")
        else:
            return myThread
    
    def stop(self):
        """Stop the thread managing the connection and join it."""
        
        self.__running = False
        if self._remoteSock != None:
            try:
                self._remoteSock.shutdown(2)
                self._remoteSock.close()
                self._remoteSock = None
            except:
                raise BluetoothManagerError("Unable to close remote socket")
        if self._mySock != None:
            try:
                self._mySock.shutdown(2)
                self._mySock.close()
                self._mySock = None
            except:
                raise BluetoothManagerError("Unable to close local socket")
        if self.__connectionThread != None:
            self.__connectionThread.join()
        self.__connectionThread = None
        self._state.update(self.STATE['none'])
        self._state.stop()
    
    def setStateCallback(self, callback, args=()):
        """Set a callback function for when connection state changes
        
        The callback is a function passed to the state Handler. It is
        called everytime the connection state changes. See the 
        BluetoothManager.STATE constant for possible states and the
        Handler docs for more information on how to write the callback.
        """
        self._state.setCallback(callback, args)
        
    def startStateCallback(self):
        """Start the listener for when connection state changes"""
        self._state.start()
        
    def stopStateCallback(self):
        """Stop the listener for when connection state changes"""
        self._state.stop()
        
    def getQueues(self):
        return [self._messageQueue, self._uiQueue]
    
    def getMessageQueueEvent(self):
        """Return the Queue of messages and it's Event
        
        The Queue is filled with messages to the script/application
        that owns this class. Because this class operates asyncronusly,
        results of calls cannot simply be returned. It is up to the
        calling script/application to take messages from the queue and
        interperate the message and handle it accordingly.
        
        The Event is set everytime a new messages is added to the
        Queue. 
        """
        return (self._messageQueue, self._messageEvent)
    
    
    # ========================Internal Methods========================
    
    def __run(self, address):
        """Private main method for the internal thread to run"""
        
        # Try to make a connection
        if address == "Server":
            result = self.__serverConnection()
        else:
            if bluetooth.is_valid_address(address):
                result = self.__clientConnection()
            else:
                raise BluetoothManagerError("Invalid MAC Address")
        
        if result == self.__SUCCESS:
            self.__connectionMade()
        else:
            self.__connectionFailed(result)
            return
            
        # Begin listening for incoming messages
        self.__listen()
    
    def __serverConnection(self):
        """Attempt to make a connection as a server."""
        
        logging.debug("__serverConnection")
        try:
            self._mySock = bluetooth.BluetoothSocket()
            self._mySock.bind(("", bluetooth.PORT_ANY))
            self._mySock.listen(1)
        except Exception as e:
            self.__connectionFailed("Failed to create a server socket.")
            raise BluetoothManagerError(e)
            return self.__FAILURE
        
        self._uiMessage("Successfully obtained a socket: " \
                         + str(self._mySock))
        
        try:
            bluetooth.advertise_service( \
                sock=self._mySock, \
                name="TerminalTexting", \
                service_id=self.uuid, \
                service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS], \
                profiles=[bluetooth.SERIAL_PORT_PROFILE] \
                )
        except:
            self.__connectionFailed("Failed to advertise the service.")
            raise BluetoothManagerError(e)
            return self.__FAILURE
        
        self._uiMessage("Awaiting connection")
        
        try:
            self._remoteSock, self._remoteInfo = \
                                            self._mySock.accept()
        except Exception as e:
            self.__connectionFailed("There was an issue accepting " \
                                    "connections.")
            raise BluetoothManagerError(e)
            return self.__FAILURE
        
        return self.__SUCCESS
    
    def __clientConnection(self, address):
        """Attempt to make a connection as a client."""
        
        try:
            foundServices = bluetooth.find_service("TerminnalTexting", \
                                                   self.uuid, \
                                                   address)
        except Exception as e:
            self.__connectionFailed("Could not search for any matching " \
                                    "braodcasts.")
            raise BluetoothManagerError(e)
            return self.__FAILURE
        
        if len(foundServices) == 0:
            self.__connectionFailed("Could not any matching services being " \
                                    "broadcasted.")
            raise BluetoothManagerError()
            return self.__FAILURE
        
        match = foundServices[0]
        self._remoteInfo = (match['host'], match['port'])
        self._remoteSock = bluetooth.BluetoothSocket()
        try:
            self._remoteSock.connect(self._remoteInfo)
        except Exception as e:
            self.__connectionFailed("Error when connecting to device")
            raise BluetoothManagerError(e)
            return self.__FAILURE
        
        return self.__SUCCESS
    
    def __connectionMade(self):
        """Update the state and message the ui"""
        self._state.update(self.STATE['connected'])
        self._uiMessage("Connection Successful\nTarget: " \
                         + str(self._remoteInfo))
    
    def __connectionFailed(self, reason):
        """Update the state and message the ui"""
        self._state.update(self.STATE['none'])
        self._uiMessage("Connection Failed\nReason: " + str(reason))
        
    def __connectionLost(self, reason):
        """Update the state and message the ui"""
        self._state.update(self.STATE['none'])
        self._uiMessage("Connection Lost\nReason: " + str(reason))
    
    def __listen(self):
        """Try to recieve messages over bluetooth and pass to the ui"""
        while self._state.get() == self.STATE['connected']:
            try:
                buffer = self._remoteSock.recv(1024)
                self._recievedMessage(buffer)
            except IOError:
                self.__connectionLost("Problem listening for incoming " \
                                      "messages.")
            except AttributeError:
                return
    
    def __writeThread(self, buffer):
        """Attempt to send buffer to the connected device."""
        try:
            self._remoteSock.send(buffer)
        except IOError:
            self._uiMessage(self.WRITE_FAILED)
        else:
            self._uiMessage(self.WRITE_SENT)
            
    def _recievedMessage(self, message):
        """Add message to the messageQueue"""
        logging.info(str(message))
        self._messageQueue.put(message)
        self._messageEvent.set()
        
    
    def _uiMessage(self, message):
        """Add message to the uiQueue"""
        self._uiQueue.put(message)
        self._uiEvent.set()
    
    
class BluetoothManagerError(Exception):
    """Generic Exception raised for issue with the manager"""  
    pass      
    
class BluetoothWriteError(Exception):
    """Exception raised when trying to write without a connection"""
    pass
    
    
    
    
    