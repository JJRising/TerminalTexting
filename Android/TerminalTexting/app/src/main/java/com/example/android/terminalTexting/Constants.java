package com.example.android.terminalTexting;

public interface Constants {

    // Broadcast keys from the Bluetooth Service back to the UI
    String CONNECTED_ACTION =
            "com.example.android.terminalTexting.action.CONNECTED";
    String FAILED_CONNECTION_ACTION =
            "com.example.android.terminalTexting.action.FAILED_CONNECTION";
    String LOST_CONNECTION_ACTION =
            "com.example.android.terminalTexting.action.LOST_CONNECTION";
    String NEW_STATE_ACTION =
            "com.example.android.terminalTexting.action.NEW_STATE";
    // Extras
    String DEVICE_NAME = "Device Name";
    String DEVICE_ADDRESS = "Device Address";
    String BLUETOOTH_STATE = "Bluetooth State";

    // Constants for the state
    int STATE_NONE = 0;
    int STATE_CONNECTING = 1;
    int STATE_CONNECTED = 2;

    // Intent actions for the Binding of the BluetoothService
    String REQUEST_UPDATE_ACTION =
            "com.example.android.terminalTexting.action.REQUEST_UPDATE";
    String WRITE_TO_REMOTE_DEVICE_ACTION =
            "com.example.android.terminalTexting.action.WRITE_TO_REMOTE_DEVICE";
    String STOP_CURRENT_CONNECTION_ACTION =
            "com.example.android.terminalTexting.action.STOP_CURRENT_CONNECTION_ACTION";

    String MESSAGE_TO_WRITE = "Message To Write";
}
