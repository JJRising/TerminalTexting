'''
Created on Mar 3, 2019

@author: jj
'''

from src import bluetoothManager

if __name__ == '__main__':
    phoneNumber = "+14166704782"
    message = "This is a much longer message that is quite long indeed. I " \
              "don't even know how long this message is it's so long. " \
              "extend it even further and make it a very long message."
    print(f"Message length: {len(message)}")
    output = bluetoothManager.getBytes(phoneNumber, message)
    print(f"output: {output}")
    
    