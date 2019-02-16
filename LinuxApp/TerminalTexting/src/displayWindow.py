'''
Created on Jan 27, 2019

@author: jj
'''

import threading
from queue import Queue


class ColorSet():
    """A python dictionary for curses color pairs."""
    def __init__(self):
        self.myDic = {}
        
    def set(self, identifier, pair):
        """Add and new entry to the dictionry"""
        self.myDic.update({identifier: pair})
        
    def g(self, identifier):
        """Returns an entry from the dictionry"""
        return self.myDic[identifier]


class DisplayWindow():
    """"A scrolling window that allows the printing of string entries
    
    Public Methods:
        getQueue()
        addEntry()
        stop()
    """

    def __init__(self, win, colorSet, displayLock):
        """Constructor.
        
        Remember to stop the running thread with the stop() method
        before the application terminates.
        """
        
        self.__win = win
        win.scrollok(True)
        self.__maxY, self.__maxX = win.getmaxyx()
        # Thread attributes
        self.__running = True
        self.__myQueue = Queue()
        self.__eventFlag = threading.Event()
        self.displayLock = displayLock
        self.__myThread = threading.Thread(target=self.__run)
        self.__myThread.start()
        self.__colorSet = colorSet
        self.__win.refresh()
    
    def getQueue(self):
        """Returns the DisplayWindow's internal Queue"""
        return self.__myQueue
    
    def addEntry(self, title, titleColor, message):
        """Prints the  title and message to the bottom of the display
        
        All text currently in the window is scrolled up. Title is
        printed in the specified color and the message is subsequently
        printed in the terminals default color.
        """
        
        self.__myQueue.put([title, self.__colorSet.g(titleColor), message])
        self.__eventFlag.set()
                    
    def stop(self):
        """Stop the running thread."""
        
        self.__running = False
        self.__eventFlag.set()
        self.__myThread.join()
        
    # ========================Internal Methods========================
        
    def __run(self):
        """Main function for the internal thread to run"""
        
        while self.__running:
            self.__eventFlag.wait()
            self.__eventFlag.clear()
            while not self.__myQueue.empty():
                lt = self.__myQueue.get()
                self.__printTitleLine(lt)
                while lt[2]:
                    self.__println(lt)
                self.__win.refresh()
                    
    def __printTitleLine(self, lt):
        """Prints the title in color and as much the message can fit.
        
        Assumes the title is smaller than the number of characters that
        can fit on a single line. Prints the title and as much of the 
        message that can fit on the rest of the line. Mutates the list
        to remove the charactes that have been printed. If all
        characters from the message have been printed, destroys the
        list. 
        """
        
        title = lt[0]
        title = title + " " # Adds a space
        color = lt[1]
        message = lt[2]
        lineLenghtRemaining = self.__maxX
        
        self.displayLock.acquire()
        # Print the title
        self.__win.move(self.__maxY - 1, 0)  # Move to start of last line
        self.__win.scroll()
        self.__win.addstr(title, color)
        lineLenghtRemaining = lineLenghtRemaining - len(title)
        
        # Print the start of the message
        if len(message) <= lineLenghtRemaining:
            self.__win.addstr(message)
            lt[2] = None
        else:
            tmp = message[:lineLenghtRemaining]
            message = message[lineLenghtRemaining:]
            lt[2] = message
            self.__win.addstr(tmp)
        self.displayLock.release()
        
    def __println(self, lt):
        """Prints the next line of the message"""
        
        message = lt[2]
        lineLenghtRemaining = self.__maxX
        
        self.displayLock.acquire()
        
        self.__win.move(self.__maxY - 1, 0)  # Move to start of last line
        self.__win.scroll()
        
        # Print the start of the message
        if len(message) <= lineLenghtRemaining:
            self.__win.addstr(message)
            lt[2] = None
        else:
            tmp = message[:lineLenghtRemaining]
            message = message[lineLenghtRemaining:]
            lt[2] = message
            self.__win.addstr(tmp)
            
        self.displayLock.release()
        
    
        
        
        
