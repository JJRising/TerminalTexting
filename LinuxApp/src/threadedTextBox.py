'''
Created on Jan 26, 2019

@author: jj
'''

import curses.textpad
from threading import Thread, Event
from queue import Queue


class ThreadedTextBox(curses.textpad.Textbox):
    '''Extention of a curses Textbox that runs on a dedicated thread.
    
    A seperate thread is created upon construction that is listening
    for user input. This textbox should be used in situations where it
    is the only point of user input in the application.
    
    Built as a finite state machine with 4 states: START, COMMAND,
    EDIT, and EXIT. The COMMAND state is only listening for single key
    commands (usually CTRL-key), while the EDIT state allows for text
    editing for the textbox with a end behaviour of gathering or
    abandoning the entered text.
    
    I personally didn't like how the Emacs-like key bindings were set
    for controlloing the cursor. I wanted to make them available for
    executing application-level commands. Thus much of the Textbox
    implementation has been overided to support this behaviour.
    
    Public Overrideable Constants:
        EDIT_CANCEL_KEY
        EDIT_CONFIRM_KEY
    
    Public Methods:
        getInput()
        startEdit()
        getMessage()
        stop()
        clear()
    '''
    
    __STATE = {'start': "START", \
               'command': "COMMAND", \
               'edit': "EDIT", \
               'exit': "EXIT"}
    __VALUE = {'cancel': "CANCEL",
               'confirm': "CONFIRM"}

    def __init__(self, win):
        """Constructor.
        
        Remember to stop the running thread with the stop() method
        before the application terminates.
        """
        curses.textpad.Textbox.__init__(self, win)
        self.__state = self.__STATE['start']
        self.__myQueue = Queue()
        self.__messageBuffer = None
        self.__gatherFlag = Event()
        self.EDIT_CANCEL_KEY = curses.ascii.ENQ       # ^E
        self.EDIT_CONFIRM_KEY = curses.ascii.VT       # ^K
        self.win.refresh()
        # Thread related bariables
        self.__running = True
        self.__myThread = Thread(target=self.__run)
        self.__myThread.start()
        
    def getInput(self, blocking=True):
        """Return the last key pressed.
        
        Will return the first key stroke available in the Queue. It is
        up to the caller to determine if the key stroke is valid or
        not. If the Queue is empty, will block until a key stroke
        entres the Queue unless blocking is set to false (in which
        case a python 'None' value is returned.
        """
        return self.__myQueue.get(block=blocking)
    
    def cancel(self):
        """Put a python None to allow getInput() to pass."""
        self.__myQueue.put('pass')
    
    def startEdit(self):
        """Begin an edit sequence."""
        self.__state = self.__STATE['edit']
    
    def getMessage(self):
        """Return entered text after an edit sequence.
        
        Will return the contents of the TextBox if the confirm key is
        pressed. Will return a python 'None' value is the cancel key is
        pressed. 
        """
        self.__state = self.__STATE['edit']
        self.__gatherFlag.wait()
        self.__gatherFlag.clear()
        self.clear()
        return self.__messageBuffer
    
    def stop(self):
        """Stop the running thread.
        
        Requires a subsiquent key press for the thread to escape the
        while loop.
        """
        self.__running = False
        self.__myThread.join()
        
    def clear(self):
        """Clear the contents of the TextBox"""
        self.win.clear()
        
    # ========================Internal Methods========================
        
    def __run(self):
        """Main method for the member thread to run."""
        self.__state = self.__STATE['command']
        while self.__running:
            key = self.win.getch()
            if self.__state == self.__STATE['command']:
                self.__myQueue.put(key)
            elif self.__state == self.__STATE['edit']:
                ret = self.edit(key)
                if ret:
                    if ret == self.__VALUE['cancel']:
                        self.__messageBuffer = None
                    else:
                        self.__messageBuffer = ret
                    self.__gatherFlag.set()
                    self.__state = self.__STATE['command']
                
    def edit(self, ch, validate=None):
        """Override of the subclass' method. NOT an entry point!"""
        
        if validate:
            ch = validate(ch)
        if not ch:
            return False
        ret = self.do_command(ch)
        if ret:
            if ret == self.__VALUE['cancel']:
                return ret
            elif ret == self.__VALUE['confirm']:
                return self.gather()
        self.win.refresh()
        return False    # Will reloop for new character
    
    def do_command(self, ch):
        """Override of the subclass' method. NOT an entry point!"""
        
        self._update_max_yx()
        (y, x) = self.win.getyx()
        self.lastcmd = ch
        if curses.ascii.isprint(ch):
            if y < self.maxy or x < self.maxx:
                self._insert_printable_char(ch)
        elif ch in (curses.ascii.STX,curses.KEY_LEFT, \
                    curses.ascii.BS,curses.KEY_BACKSPACE):
            if x > 0:
                self.win.move(y, x-1)
            elif y == 0:
                pass
            elif self.stripspaces:
                self.win.move(y-1, self._end_of_line(y-1))
            else:
                self.win.move(y-1, self.maxx)
            if ch in (curses.ascii.BS, curses.KEY_BACKSPACE):
                self.win.delch()
        elif ch == curses.KEY_RIGHT:
            if x < self.maxx:
                self.win.move(y, x+1)
            elif y == self.maxy:
                pass
            else:
                self.win.move(y+1, 0)
        elif ch == curses.KEY_DOWN:
            if y < self.maxy:
                self.win.move(y+1, x)
                if x > self._end_of_line(y+1):
                    self.win.move(y+1, self._end_of_line(y+1))
        elif ch == curses.KEY_UP:
            if y > 0:
                self.win.move(y-1, x)
                if x > self._end_of_line(y-1):
                    self.win.move(y-1, self._end_of_line(y-1))
        elif ch == self.EDIT_CANCEL_KEY:
            return self.__VALUE['cancel']
        elif ch == self.EDIT_CONFIRM_KEY:
            return self.__VALUE['confirm']
        
        return False    # Will reloop for new character
    
    def gather(self):
        """Extends the subclass' method"""
        
        ret = curses.textpad.Textbox.gather(self)
        ret = ret.replace("\n", "")
        ret = ret.strip(" ")
        return ret
        
        
        
        
        
        