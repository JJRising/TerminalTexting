'''
Created on Feb 25, 2019

@author: jj
'''

import curses.textpad

class Tbox(curses.textpad.Textbox):
    '''
    classdocs
    '''
    
    OUTPUT_GATHER = "gatherComplete"
    OUTPUT_CANCEL = "gatherCancel"

    def __init__(self, win, outputQueue):
        '''
        Constructor
        '''
        super(Tbox, self).__init__(win)
        self.output = outputQueue
        self.win.refresh()
        
    def clear(self):
        self.win.clear()
        self.win.move(0,0)
        self.win.refresh()
    
    def gather(self):
        """Extends the subclass' method"""
        
        ret = curses.textpad.Textbox.gather(self)
        ret = ret.replace("\n", "")
        ret = ret.strip(" ")
        return ret
    
    def getInput(self):
        return self.win.getch()
        
    def do_command(self, ch):
        "Process a single editing command."
        self._update_max_yx()
        (y, x) = self.win.getyx()
        self.lastcmd = ch
        if curses.ascii.isprint(ch):
            if y < self.maxy or x < self.maxx:
                self._insert_printable_char(ch)
        elif ch in (curses.KEY_LEFT,curses.KEY_BACKSPACE):
            if x > 0:
                self.win.move(y, x-1)
            elif y == 0:
                pass
            elif self.stripspaces:
                self.win.move(y-1, self._end_of_line(y-1))
            else:
                self.win.move(y-1, self.maxx)
            if ch == curses.KEY_BACKSPACE:
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
        self.win.refresh()
        
        
        
        
        