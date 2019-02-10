'''
Created on Jan 31, 2019

@author: jj
'''

class State():
    """TODO: Class Doc"""
    
    def __init__(self, fsm, name, enter=None, run=None, exit=None):
        self.fsm = fsm
        self.name = name
        self.targets = []
        if enter:
            self.enter = enter
        if run:
            self.run = run
        if exit:
            self.exit = exit
    
    def enter(self):
        pass
    
    def run(self):
        pass
    
    def exit(self):
        pass

class FSM():
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.states = [State("Start"), State("Exit")]
        self.currentState = 0
        self.newState = 0
        self.FSMBoolean = True
        
    def main(self):
        while self.FSMBoolean:
            if self.newState != self.currentState:
                self.states[self.newState].enter(self)
            self.currentState = self.newState
            self.states[self.currentState].run(self)
            if self.newState != self.currentState:
                self.states[self.currentState].exit(self)
                
    def target(self, name):
        for i in range(0,len(self.states)):
            if self.states[i].name == name:
                return i
        raise FSMError()
    
    def addState(self, state):
        self.states.append(state)
        
        
class FSMError(Exception):
    pass

