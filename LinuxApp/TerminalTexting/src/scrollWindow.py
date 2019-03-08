'''
@author: jj
'''

class ScrollWindow():
    '''Contains a curses window and methods to print to it.'''

    def __init__(self, win):
        self.win = win
        win.scrollok(True)
        self.__maxY, self.__maxX = win.getmaxyx()
        self.win.refresh()
        
    def addEntry(self, title, titleColor, message):
        """Scrolls all text up and inserts a new enrty to the bottom
        
        title - String containing the text to be printed as the title
        titleColor - curses colorPair object for the title String
        message - String for the base message
        """
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
        else: # break the string up into printable sections
            tmp = text[:lineLengthRemaining]
            text = text[lineLengthRemaining:-1]
            self.win.addstr(tmp)
            self._println(text)