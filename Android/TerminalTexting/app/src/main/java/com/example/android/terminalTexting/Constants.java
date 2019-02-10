package com.example.android.terminalTexting;

public interface Constants {

    // Intent Actions
    String BROADCAST_ACTION =
            "com.example.android.terminalTexting.action.BORADCAST";

    // Message types sent from the BluetoothChatService Handler
    int MESSAGE_STATE_CHANGE = 1;
    int MESSAGE_READ = 2;
    int MESSAGE_WRITE = 3;
    int MESSAGE_DEVICE_NAME = 4;
    int MESSAGE_TOAST = 5;
    int MESSAGE_TEXTLOG = 6;
    int MESSAGE_CONNECTION_FAILED = 7;
    int MESSAGE_CONNECTION_LOST = 8;

    // Key names received from the BluetoothChatService Handler
    String DEVICE_NAME = "device_name";
    String TOAST = "toast";
    String TEXT = "text";

    // Constants for the state
    int STATE_NONE = 0;
    int STATE_CONNECTING = 1;
    int STATE_CONNECTED = 2;
}
