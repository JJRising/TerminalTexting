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
        self.__state = Handler(self.STATE['none'])
        self.__mySock = None            # Socket for this device
        self.__remoteSock = None        # Socket for the remote device
        self.__remoteInfo = None
        self.__messageQueue = Queue()
        self.__uiQueue = Queue()
        if uiEvent == None:
            self.__messageEvent = Event()
            self.__uiEvent = Event()
        else:
            self.__messageEvent = uiEvent
            self.__uiEvent = uiEvent
        # Thread related variables
        self.__connectionThread = None
        self.__running = False
        self._uiMessage("BluetoothManager established!")
    
    def connectAsServer(self):
        """Entry Point (1/2). Attempt to allow connection as a server.
        
        Forks a new connection thread passing 'Server' along as an 
        argument'
        """
        if self.__state.get() == self.STATE['none']:
            self.__running = True
            self.__state.update(self.STATE['connecting'])
            self.__connectionThread = \
                            Thread(target=self.__run, args=("Server",))
            self.__connectionThread.start()
    
    def connectAsClient(self, macAddress):
        """Entry Point (1/2). Attempt to make connection as a client.
        
        Forks a new connection thread passing the macAddress along as
        an argument'
        """
        if self.__state.get() == self.STATE['none']:
            self.__state.update(self.STATE['connecting'])
            self.__running = True
            self.__connectionThread = \
                            Thread(target=self.__run, args=(macAddress,))
            self.__connectionThread.start()
          
    def isConnected(self):
        """Return True if there is a current connection"""
        return self.__state.get() == self.STATE['connected']
    
    def who(self):
        """Return the name and MAC_ADDRESS of the connection"""
        return self.__remoteInfo
    
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
        if self.__state.get() != self.STATE['connected']:
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
        if self.__remoteSock != None:
            try:
                self.__remoteSock.shutdown(2)
                self.__remoteSock.close()
                self.__remoteSock = None
            except:
                raise BluetoothManagerError("Unable to close remote socket")
        if self.__mySock != None:
            try:
                self.__mySock.shutdown(2)
                self.__mySock.close()
                self.__mySock = None
            except:
                raise BluetoothManagerError("Unable to close local socket")
        if self.__connectionThread != None:
            self.__connectionThread.join()
        self.__connectionThread = None
        self.__state.update(self.STATE['none'])
        self.__state.stop()
    
    def setStateCallback(self, callback, args=()):
        """Set a callback function for when connection state changes
        
        The callback is a function passed to the state Handler. It is
        called everytime the connection state changes. See the 
        BluetoothManager.STATE constant for possible states and the
        Handler docs for more information on how to write the callback.
        """
        self.__state.setCallback(callback, args)
        
    def startStateCallback(self):
        """Start the listener for when connection state changes"""
        self.__state.start()
        
    def stopStateCallback(self):
        """Stop the listener for when connection state changes"""
        self.__state.stop()
        
    def setStateCallbaak(self, callback, args=()):
        self.__state.setCallback(callback, args)
        
    def getQueues(self):
        return [self.__messageQueue, self.__uiQueue]
    
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
        return (self.__messageQueue, self.__messageEvent)
    
    
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
            self.__mySock = bluetooth.BluetoothSocket()
            self.__mySock.bind(("", bluetooth.PORT_ANY))
            self.__mySock.listen(1)
        except Exception as e:
            self.__connectionFailed("Failed to create a server socket.")
            raise BluetoothManagerError(e)
            return self.__FAILURE
        
        self._uiMessage("Successfully obtained a socket: " \
                         + str(self.__mySock))
        
        try:
            bluetooth.advertise_service( \
                sock=self.__mySock, \
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
            self.__remoteSock, self.__remoteInfo = \
                                            self.__mySock.accept()
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
        self.__remoteInfo = (match['host'], match['port'])
        self.__remoteSock = bluetooth.BluetoothSocket()
        try:
            self.__remoteSock.connect(self.__remoteInfo)
        except Exception as e:
            self.__connectionFailed("Error when connecting to device")
            raise BluetoothManagerError(e)
            return self.__FAILURE
        
        return self.__SUCCESS
    
    def __connectionMade(self):
        """Update the state and message the ui"""
        self.__state.update(self.STATE['connected'])
        self._uiMessage("Connection Successful\nTarget: " \
                         + str(self.__remoteInfo))
    
    def __connectionFailed(self, reason):
        """Update the state and message the ui"""
        self.__state.update(self.STATE['none'])
        self._uiMessage("Connection Failed\nReason: " + str(reason))
        
    def __connectionLost(self, reason):
        """Update the state and message the ui"""
        self.__state.update(self.STATE['none'])
        self._uiMessage("Connection Lost\nReason: " + str(reason))
    
    def __listen(self):
        """Try to recieve messages over bluetooth and pass to the ui"""
        while self.__state.get() == self.STATE['connected']:
            try:
                buffer = self.__remoteSock.recv(1024)
                self._recievedMessage(buffer)
            except IOError:
                self.__connectionLost("Problem listening for incoming " \
                                      "messages.")
            except AttributeError:
                return
    
    def __writeThread(self, buffer):
        """Attempt to send buffer to the connected device."""
        try:
            self.__remoteSock.send(buffer)
        except IOError:
            self._uiMessage(self.WRITE_FAILED)
        else:
            self._uiMessage(self.WRITE_SENT)
            
    def _recievedMessage(self, message):
        """Add message to the messageQueue"""
        logging.info(str(message))
        self.__messageQueue.put(message)
        self.__messageEvent.set()
        
    
    def _uiMessage(self, message):
        """Add message to the uiQueue"""
        self.__uiQueue.put(message)
        self.__uiEvent.set()
    
    
class BluetoothManagerError(Exception):
    """Generic Exception raised for issue with the manager"""  
    pass      
    
class BluetoothWriteError(Exception):
    """Exception raised when trying to write without a connection"""
    pass
    
    
    
    
    