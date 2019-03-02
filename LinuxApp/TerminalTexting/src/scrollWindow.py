'''
Created on Feb 25, 2019

@author: jj
'''

class ScrollWindow():
    '''
    classdocs
    '''

    def __init__(self, win):
        '''
        Constructor
        '''
        self.win = win
        win.scrollok(True)
        self.__maxY, self.__maxX = win.getmaxyx()
        self.win.refresh()
        
    def addEntry(self, title, titleColor, message):
        self._printTitleLine(title, titleColor)
        self._println(message)
        self.win.refresh()
    
    def _printTitleLine(self, title, titleColor):
        self.win.move(self.__maxY - 1, 1) # Move to start of last line
        self.win.scroll()
        self.win.addstr(title, titleColor)
        
    def _println(self, text):
        lineLengthRemaining = self.__maxX - 4
        
        self.win.move(self.__maxY - 1, 1) # Move to start of last line
        self.win.scroll()
        
        if len(text) <= lineLengthRemaining:
            self.win.addstr(text)
        else:
            tmp = text[:lineLengthRemaining]
            text = text[lineLengthRemaining:-1]
            self.win.addstr(tmp)
            self._println(text)