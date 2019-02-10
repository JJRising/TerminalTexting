package com.example.android.terminalTexting;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

/**
 * This class is designed to manage the bluetooth connection between the android device and a
 * given remote device. A single instance of this class will handle one connection only. Create
 * another instance to handle additional connections.
 */
class BluetoothConnectionService {
    // Debugging
    private static final String LOG_TAG = "BluetoothChatService";

    private final BluetoothAdapter mAdapter;
    private final Handler mHandler;
    private ConnectThread mConnectThread;
    private MessageThread mMessageThread;
    private int mState;
    private int mNewState;

    // Unique UUID for this application
    private static final UUID MY_UUID_SECURE =
            UUID.fromString("56abddf0-d4d2-45c7-9b2b-7837582d436f");
    private static final UUID MY_UUID_INSECURE =
            UUID.fromString("d2d51468-54fd-4eb2-8ffa-7837582d436f");

    BluetoothConnectionService(Handler handler) {
        mAdapter = BluetoothAdapter.getDefaultAdapter();
        mState = Constants.STATE_NONE;
        mNewState = mState;
        mHandler = handler;
    }

    private synchronized int getState() { return mState; }

    private synchronized void updateUserInterface() {
        Log.d(LOG_TAG, "updateUserInterfaceTitle() " + mNewState + " -> " + mState);
        mNewState = mState;

        mHandler.obtainMessage(Constants.MESSAGE_STATE_CHANGE, mNewState, -1).sendToTarget();
    }

    synchronized void connect(BluetoothDevice device, boolean secure) {
        Log.d(LOG_TAG, "connect to: " + device);

        // Cancel any thread attempting to make a connection
        if (mState == Constants.STATE_CONNECTING) {
            if (mConnectThread != null) {
                mConnectThread.cancel();
                mConnectThread = null;
            }
        }
        // Cancel any thread already connected
        if (mMessageThread != null) {
            mMessageThread.cancel();
            mMessageThread = null;
        }

        // Start the thread to connect with the given device
        mConnectThread = new ConnectThread(device, secure);
        mConnectThread.start();

        // Update the UI
        updateUserInterface();
    }

    private synchronized void connected(BluetoothSocket socket, BluetoothDevice device,
                                        final String socketType) {
        Log.d(LOG_TAG, "connected, Socket Type:" + socketType);

        // Cancel the thread that completed the connection
        if (mConnectThread != null) {
            mConnectThread.cancel();
            mConnectThread = null;
        }

        // Cancel any thread currently running a connection
        if (mMessageThread != null) {
            mMessageThread.cancel();
            mMessageThread = null;
        }

        mMessageThread = new MessageThread(socket, socketType);
        mMessageThread.start();

        // Send the name of the connected device back to the UI Activity
        Message msg = mHandler.obtainMessage(Constants.MESSAGE_DEVICE_NAME);
        Bundle bundle = new Bundle();
        bundle.putString(Constants.DEVICE_NAME, device.getName());
        msg.setData(bundle);
        mHandler.sendMessage(msg);
        // Update the UI
        updateUserInterface();
    }

    synchronized void stop() {
        Log.d(LOG_TAG, "stop");

        if (mConnectThread != null) {
            mConnectThread.cancel();
            mConnectThread = null;
        }
        if (mMessageThread != null) {
            mMessageThread.cancel();
            mMessageThread = null;
        }
        mState = Constants.STATE_NONE;

        // Update the UI
        updateUserInterface();
    }

    private synchronized void connectionFailed() {
        // Send a failure message back to the Activity
        Message msg = mHandler.obtainMessage(Constants.MESSAGE_TOAST);
        Bundle bundle = new Bundle();
        bundle.putString(Constants.TOAST, "Unable to connect device");
        msg.setData(bundle);
        mHandler.sendMessage(msg);

        mState = Constants.STATE_NONE;

        // Update the UI
        updateUserInterface();
    }

    private synchronized void connectionLost() {
        // Send a failure message back to the Activity
        Message msg = mHandler.obtainMessage(Constants.MESSAGE_TOAST);
        Bundle bundle = new Bundle();
        bundle.putString(Constants.TOAST, "Device connection was lost");
        msg.setData(bundle);
        mHandler.sendMessage(msg);

        mState = Constants.STATE_NONE;

        // Update the UI
        updateUserInterface();
    }

    void write(byte[] out) {
        // Create temporary object
        MessageThread r;
        // Synchronize a copy of the ConnectedThread
        synchronized (this) {
            if (mState != Constants.STATE_CONNECTED) return;
            r = mMessageThread;
        }
        // Perform the write non-synchronized
        r.write(out);
    }

    /**
     * This thread runs while attempting to make an outgoing connection
     * with a device. It runs straight through; the connection either
     * succeeds or fails.
     */
    private class ConnectThread extends Thread {
        private final BluetoothDevice mmDevice;
        private final BluetoothSocket mmSocket;
        private String mSocketType;

        ConnectThread(BluetoothDevice device, boolean secure) {
            Log.d(LOG_TAG, "Connect Thread Created!");
            mmDevice = device;
            BluetoothSocket socket = null;
            mSocketType = secure ? "Secure" : "Insecure";

            Log.d(LOG_TAG, mmDevice.toString());

            // Get a BluetoothSocket for a connection with the
            // given BluetoothDevice
            try {
                if (secure) {
                    socket = mmDevice.createRfcommSocketToServiceRecord(MY_UUID_SECURE);
                } else {
                    socket = mmDevice.createInsecureRfcommSocketToServiceRecord(MY_UUID_INSECURE);
                }
            } catch (IOException e) {
                Log.e(LOG_TAG, "Socket Type: " + mSocketType + "create() failed", e);
            }
            Log.d(LOG_TAG, socket.toString());
            mmSocket = socket;
            mState = Constants.STATE_CONNECTING;
        }

        public void run() {
            Log.i(LOG_TAG, "BEGIN mConnectThread SocketType:" + mSocketType);
            setName("ConnectThread" + mSocketType);

            // Always cancel discovery because it will slow down a connection
            mAdapter.cancelDiscovery();

            Log.d(LOG_TAG, "attempting to connect");
            Log.d(LOG_TAG, "Socket status: " + mmSocket.toString());

            // Make a connection to the BluetoothSocket
            try {
                // This is a blocking call and will only return on a
                // successful connection or an exception
                mmSocket.connect();
            } catch (IOException e) {
                Log.e(LOG_TAG, "Unable to connect: " + e.toString());
                Log.d(LOG_TAG, "isConnected: " + mmSocket.isConnected());
                try {
                    mmSocket.close();
                } catch (IOException e2) {
                    Log.e(LOG_TAG, "unable to close() " + mSocketType +
                            " socket during connection failure", e2);
                }
                connectionFailed();
                return;
            }

            // Reset the ConnectThread because we're done
            synchronized (BluetoothConnectionService.this) {
                mConnectThread = null;
            }

            // Start the connected thread
            connected(mmSocket, mmDevice, mSocketType);
        }

        void cancel() {
            try {
                mmSocket.close();
            } catch (IOException e) {
                Log.e(LOG_TAG, "close() of connect " + mSocketType + " socket failed", e);
            }
        }
    }

    /**
     * This thread runs during a connection with a remote device.
     * It handles all incoming and outgoing transmissions.
     */
    private class MessageThread extends Thread {
        private final BluetoothSocket mmSocket;
        private final InputStream mmInStream;
        private final OutputStream mmOutStream;

        MessageThread(BluetoothSocket socket, String socketType) {
            Log.d(LOG_TAG, "create ConnectedThread: " + socketType);
            mmSocket = socket;
            InputStream tmpIn = null;
            OutputStream tmpOut = null;

            // Get the BluetoothSocket input and output streams
            try {
                tmpIn = socket.getInputStream();
                tmpOut = socket.getOutputStream();
            } catch (IOException e) {
                Log.e(LOG_TAG, "temp sockets not created", e);
            }

            mmInStream = tmpIn;
            mmOutStream = tmpOut;
            mState = Constants.STATE_CONNECTED;
        }

        public void run() {
            Log.i(LOG_TAG, "BEGIN mConnectedThread");
            byte[] buffer = new byte[1024];
            int bytes;


            // Keep listening to the InputStream while connected
            while (mState == Constants.STATE_CONNECTED) {
                try {
                    // Read from the InputStream
                    bytes = mmInStream.read(buffer);

                    // Send the obtained bytes to the UI Activity
                    mHandler.obtainMessage(Constants.MESSAGE_READ, bytes, -1, buffer)
                            .sendToTarget();
                } catch (IOException e) {
                    Log.e(LOG_TAG, "disconnected", e);
                    connectionLost();
                    break;
                }
            }
        }

        void write(byte[] buffer) {
            try {
                mmOutStream.write(buffer);

                // Share the sent message back to the UI Activity
                mHandler.obtainMessage(Constants.MESSAGE_WRITE, -1, -1, buffer)
                        .sendToTarget();
            } catch (IOException e) {
                Log.e(LOG_TAG, "Exception during write", e);
            }
        }

        void cancel() {
            try {
                mmSocket.close();
            } catch (IOException e) {
                Log.e(LOG_TAG, "close() of connect socket failed", e);
            }
        }
    }
}
