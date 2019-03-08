'''
@author: jj
'''

class ColorSet():
    """A python dictionary for curses color pairs."""
    
    def __init__(self):
        self.myDic = {}
        
    def set(self, identifier, pair):
        """Add and new entry to the dictionry"""
        self.myDic.update({identifier: pair})
        return self
        
    def get(self, identifier):
        """Returns an entry from the dictionry"""
        return self.myDic[identifier]