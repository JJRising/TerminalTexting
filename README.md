# TerminalTexting
Personal project I've been working on to experiment with Bluetooth communication between my phone and laptop. It involves a terminal application writen in python leveraging the curses library and the pyBluez project as well as and android application.

## Overview
This project contains two main portions. The first of which is an Android app. It listens for incoming SMS, packages them into a byte array, and sends them over a serial bluetooth connection. The second portion is a terminal application that recieves the byte array from the android device and displays it. It also allows the option for the user to write and send text messages from the android device inside the terminal window.

## Getting Started
### Android Side
The android studio project contains all the code for a deployable app. You can pull the project and open it in Android Studio. Alternitively, you can download the apk file and install the app that way.

Once you have the app running, click "Connect to a new device..." to bring up the device list. Select a device to connect to or scan for available devices. Selecting a device will begin a client side connection process. You will need the terminal application running a server side connection in order for the connectinon to be made or a timeout will occur.

Once a connection has been made, the background service will immediately begin listening for incoming SMS and pushing them to bluetooth as well as be available to send SMS recieved over bluetooth.

### Terminal Side
The Terminal application uses curses and thus needs to be launched from a terminal window. It will also require sudo user privilagies due to the protections most OSs put on bluetooth periferals.

Once running, follow the on screen instructions to begin a server connection (client connection not yet implemented). This allows a client connection from the Android Side. Once a connection is made, incoming SMS will be printed to the display. You can then reply to the last recieved message or compose a new message to send. When composing, you will be prompt for a phone number to send the SMS to. Follow the North American standard of "+1" followed by the 10 digit number.

## Dependancies
- [Python3](https://www.python.org/)
- ncurses (should already be a part of your OS) - [Windows](https://pypi.org/project/windows-curses/) [Linux](https://www.ostechnix.com/how-to-install-ncurses-library-in-linux/)
- [PyBluez](https://github.com/pybluez/pybluez)

It should be noted, that this has been tested on a Linux OS and simply requires a configured bluetooth adapter and sudo user privligies. You will need aditional privligies on Windows. See the PyBluez project for more details.

## Future Development
- Currently, the only connection option is to have the andorid device act as a client and the terminal application act as the server. The skeleton for the reverse exists in the code but is not yet implemented.
- There is an i ssue with pybluez where closeing the local sockets does not cause the recv() method to return with an error so connectings can only be closed from the android side.
- Will likely use this project to experiment with other user interface options.

## Legal
This project is licensed under the GNU General Public License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments
Special thanks to whomever it is at Google that wrote the [Android BluetoothChat Sample](https://github.com/googlesamples/android-BluetoothChat) project for providing code inspiration for the android side bluetooth service.

Also thanks to all the contributers of the curses library in python, and the pybluez project.
