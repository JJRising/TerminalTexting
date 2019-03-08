'''
@author: jj
'''

class TextBar():
    '''A class for a single line of text window
    
    win - a curses window object
    colorPair - a curses colorPair object
    '''


    def __init__(self, win, colorPair):
        self.win = win
        self.pair = colorPair
        self.win.bkgd(' ', self.pair)
        self.win.refresh()
        
    def update(self, text):
        self.win.attron(self.pair)
        self.win.erase()
        self.win.addstr(text)
        self.win.attroff(self.pair)
        self.win.refresh()