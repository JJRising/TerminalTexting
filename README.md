# TerminalTexting
Personal project I've been working on to experiment with Bluetooth communication between my phone and laptop. It involves a terminal application writen in python leveraging the curses library and the pyBluez project as well as and android application.

## Overview
This project contains two main portions. The first of which is an Android app. It listens for incoming SMS, packages them into a byte array, and sends them over a serial bluetooth connection. The second portion is a terminal application that recieves the byte array from the android device and displays it. It also allows the option for the user to write and send text messages from the android device inside the terminal window.

## Getting Started
The android studio project contains all the code for a deployable app. You can pull the project and open it in Android Studio. Alternitively, you can download the apk file and install the app that way.
The Linux application uses curses and thus needs to be launched from a terminal window. It will also require sudo user privilagies due to the protections most OSs put on bluetooth periferals.

## Dependancies
- [Python3](https://www.python.org/)
- ncurses (should already be a part of your OS) - [Windows](https://pypi.org/project/windows-curses/) [Linux](https://www.ostechnix.com/how-to-install-ncurses-library-in-linux/)
- [PyBluez](https://github.com/pybluez/pybluez)

## Future Development
- Currently, the only connection option is to have the andorid device act as a client and the terminal application act as the server. The skeleton for the reverse exists in the code but is not yet implemented.
- There is an issue with pybluez where closeing the local sockets does not cause the recv() method to return with an error so connectings can only be closed from the android side.
- Will likely use this project to experiment with other user interface options.

## Legal
This project is licensed under the GNU General Public License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments
Special thanks to whomever it is at Google that wrote the [Android BluetoothChat Sample](https://github.com/googlesamples/android-BluetoothChat) project for providing code inspiration for the android side bluetooth service.

Also thanks to all the contributers of the curses library in python, and the pybluez project.
