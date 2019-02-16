
from src import bluetoothManager
import logging

macAddress = "C0:EE:FB:27:43:16"
UUID = "56abddf0-d4d2-45c7-9b2b-7837582d436f"

def main():
    logging.basicConfig(filename='log.log', filemode='w', level=logging.DEBUG)
    logging.info("Logging started")
    btman = bluetoothManager.BluetoothManager(UUID)
    btman.connectAsServer()
    btman.stop()
    logging.info("Done")

if __name__ == '__main__':
    main()
