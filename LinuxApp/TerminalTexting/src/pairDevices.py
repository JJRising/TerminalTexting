'''
Created on Jan 16, 2019

@author: jj
'''

import subprocess

def pair(macAddress):
    subprocess.call(["bluetoothctl","power","on"])
    subprocess.call(["bluetoothctl","discoverable","on"])
    process = subprocess.Popen(["bluetoothctl", "devices"], \
                               stdout=subprocess.PIPE)
    pairedDevices = str(process.communicate())
    if(pairedDevices.find(macAddress) == -1):
        import signal
        def handler(signum, frame):
            print("Signal Timeout")
            raise IOError("Couldn't find the device!")

        def bluetoothScan():
            proc = subprocess.Popen(["bluetoothctl","scan","on"], \
                                    stdout=subprocess.PIPE)
            while proc.poll() is None:
                output = proc.stdout.readline()
                if(output.find(macAddress) != -1):
                    proc.terminate()
                    signal.alarm(0)

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(15)

        try:
            bluetoothScan()
        except IOError:
            return 0 # Could not find device

        subprocess.call(["bluetoothctl","pair",macAddress])
        subprocess.call(["bluetoothctl","trust",macAddress]) 
    
    subprocess.call(["bluetoothctl","discoverable","off"])
    return 1 # Found and paired with the device
