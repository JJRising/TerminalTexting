'''
Created on Feb 25, 2019

@author: jj
'''

class TextBar():
    '''
    classdocs
    '''


    def __init__(self, win, colorPair):
        '''
        Constructor
        '''
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