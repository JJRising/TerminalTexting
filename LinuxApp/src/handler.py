'''
Created on Jan 28, 2019

@author: jj
'''

import threading
from queue import Queue
import logging

class Handler():
    """Wrapper of a single variable with a callback upon modification
    
    It forks a thread that runs a function 'callback()' evertime the
    base variable is updated. callback() is passed into the
    StateHandler through its parameters or the setListener() method.
    callback() should be defined outside the class and make use of the
    self.mQueue variable. The Queue should be used rather than the base
    variable due to the fact that the thread is not guaranteed to run
    before the base variable is changed again.
    """
    
    def __init__(self, var, callback=None, args=()):
        self.mVar = var
        if callback != None:
            self.running = True
        else:
            self.running = False
        self.event = threading.Event()
        self.callback = callback
        self.args = args
        self.mQueue = Queue()
        self.myThread = threading.Thread(target=self.__run)
        self.runCounter = 0
        
    def setCallback(self, callback, args=()):
        """Assign a new callback() function
        
        callback should be a function that utalizes the memeber
        variable mQueue. Functions using the member variable mVar is
        not recomended as it is not guaranteed that the thread running
        the callback function will execute before the member variable
        mVar is updated again.
        """
        self.callback = callback
        self.args = args
        
    def start(self):
        """Start the thread that listens for modification
        
        Should not be called before defining a callback function.
        """
        if self.callback == None:
            raise CallbackError("Tried to start the handler with no "
                                "callback set")
        self.running = True
        self.myThread.start()
        
    def update(self, var):
        """Modifier for the base variable
        
        Updates the base variable to a new value and adds its updated
        value to the member Queue so that it can be referenced in the
        callback function. Sets an event variable to trigger the member
        thread to run the callback function.
        """
        self.mVar = var
        self.mQueue.put(var)
        self.runCounter = self.runCounter + 1
        self.event.set()
        
    def get(self):
        """Return the base variable."""
        return self.mVar
    
    def stop(self):
        """Stop the thread that's listening for changes."""
        self.running = False
        self.event.set()
        #self.myThread.join()
    
    def __run(self):
        """Method for the thread to run"""
        self.event.wait()
        self.event.clear()
        while self.running:
            if self.callback != None:
                try:
                    self.callback(self.mVar, *self.args)
                except:
                    raise CallbackError("The callback is not callable")
            self.runCounter = self.runCounter - 1
            self.event.wait()
            self.event.clear()
        # Run through any remaining callbacks
        while self.runCounter > 0:
            if self.callback != None:
                try:
                    self.callback(self.mVar, *self.args)
                except:
                    raise CallbackError("The callback is not callable")
            self.runCounter = self.runCounter - 1
 
class CallbackError(Exception):
    def __init__(self, arg):
        self.args = (arg,)


