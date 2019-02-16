#!/usr/bin/python

'''
Created on Jan 15, 2019

@author: jj
'''

from src import cursesUI
import logging
    
macAddress = "C0:EE:FB:27:43:16"

def main():
    logging.basicConfig(filename='log.log', filemode='w', level=logging.DEBUG)
    logging.info("Logging started")
    #btman = BluetoothManager()
    #btman.connect(macAddress)
    cursesUI.startUI()

if __name__ == '__main__':
    main()

