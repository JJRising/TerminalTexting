package com.example.android.terminalTexting;

import android.app.IntentService;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Intent;
import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

/**
 * An {@link IntentService} subclass for handling asynchronous task requests in
 * a service on a separate handler thread.
 */
public class BluetoothService extends IntentService {
    // Debugging
    private static final String LOG_TAG = "TermTexting.BtService";

    // Actions the IntentService can perform
    private static final String ACTION_SERVER_CONNECT =
            "com.example.android.terminalTexting.action.SERVER_CONNECT";
    private static final String ACTION_CLIENT_CONNECT =
            "com.example.android.terminalTexting.action.CLIENT_CONNECT";
    private static final String ACTION_STOP =
            "com.example.android.terminalTexting.action.STOP";

    // Parameters
    private static final String DEVICE_ADDRESS =
            "com.example.android.terminalTexting.extra.DEVICE_ADDRESS";

    // Unique UUID for this application
    private static final UUID MY_UUID =
            UUID.fromString("56abddf0-d4d2-45c7-9b2b-7837582d436f");

    // Member variables for the service
    private final BluetoothAdapter mAdapter;
    private ConnectThread mConnectThread;
    private MessageThread mMessageThread;
    private int mState;
    private int mNewState;

    public BluetoothService() {
        super("BluetoothService");
        mAdapter = BluetoothAdapter.getDefaultAdapter();
    }

    @Override
    public void onCreate() {
        super.onCreate();
        mState = Constants.STATE_NONE;
        mNewState = mState;
    }

    @Override
    public void onDestroy() {
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
        updateUserInterfaceToNewState();

        super.onDestroy();
    }

    public static Intent getIntent(Context context){
        return new Intent(context, BluetoothService.class);
    }
//-------------------------------Service Start points----------------------------------------//

    /**
     * Starts this service to perform a bluetooth connection as a server. If
     * the service is already performing a task this action will be queued.
     */
    public static void startServerConnect(Context context, String secure) {
        Intent intent = new Intent(context, BluetoothService.class);
        intent.setAction(ACTION_SERVER_CONNECT);
        context.startService(intent);
    }

    /**
     * Starts this service to perform a bluetooth connection as a client. If
     * the service is already performing a task this action will be queued.
     */
    public static void startClientConnect(Context context, String deviceAddress) {
        Log.d(LOG_TAG, "startClientConnect");
        Intent intent = new Intent(context, BluetoothService.class);
        intent.setAction(ACTION_CLIENT_CONNECT);
        intent.putExtra(DEVICE_ADDRESS, deviceAddress);
        context.startService(intent);
    }

    public void stop(Context context) {
        Intent intent = new Intent(context, BluetoothService.class);
        intent.setAction(ACTION_STOP);
        stopService(intent);
    }

    //--------------------------------Action Handling--------------------------------------------//

    @Override
    protected void onHandleIntent(Intent intent) {
        if (intent != null) {
            final String action = intent.getAction();
            if (ACTION_SERVER_CONNECT.equals(action)) {
                handleActionServerConnect();
            } else if (ACTION_CLIENT_CONNECT.equals(action)) {
                final String deviceAddress = intent.getStringExtra(DEVICE_ADDRESS);
                handleActionClientConnect(deviceAddress);
            }
        }
    }

    /**
     * Handle action Foo in the provided background thread with the provided
     * parameters.
     */
    private void handleActionServerConnect() {
        // TODO: Handle action server connect
        throw new UnsupportedOperationException("Not yet implemented");
    }

    /**
     * Handle action Baz in the provided background thread with the provided
     * parameters.
     */
    private void handleActionClientConnect(String deviceAddress) {

        BluetoothDevice device = mAdapter.getRemoteDevice(deviceAddress);

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
        mConnectThread = new ConnectThread(device);
        mConnectThread.start();

        // Update the UI
        updateUserInterfaceToNewState();
    }

    //--------------------------------User Feedback----------------------------------------------//

    private synchronized void updateUserInterfaceToConnectedDevice(String deviceName) {
        /*
        Message msg = mHandler.obtainMessage(Constants.MESSAGE_STATE_CHANGE);
        Bundle bundle = new Bundle();
        bundle.putString(Constants.DEVICE_NAME, deviceName);
        msg.setData(bundle);
        mHandler.sendMessage(msg);
        */
    }

    private synchronized void updateUserInterfaceToFailedConnection() {
        //mHandler.obtainMessage(Constants.MESSAGE_CONNECTION_FAILED).sendToTarget();
    }

    private synchronized void updateUserInterfaceToLostConnection() {
        //mHandler.obtainMessage(Constants.MESSAGE_CONNECTION_LOST).sendToTarget();
    }

    private synchronized void updateUserInterfaceToNewState() {
        Log.d(LOG_TAG, "updateUserInterfaceTitle() " + mNewState + " -> " + mState);
        mNewState = mState;

        //mHandler.obtainMessage(Constants.MESSAGE_STATE_CHANGE, mNewState, -1).sendToTarget();
    }


    //--------------------------------Connection Handling----------------------------------------//

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

        // Update the UI
        updateUserInterfaceToConnectedDevice(device.getName());
        updateUserInterfaceToNewState();
    }

    private synchronized void connectionFailed() {
        mState = Constants.STATE_NONE;

        // Update the UI
        updateUserInterfaceToFailedConnection();
        updateUserInterfaceToNewState();
    }

    private synchronized void connectionLost() {
        mState = Constants.STATE_NONE;

        // Update the UI
        updateUserInterfaceToLostConnection();
        updateUserInterfaceToNewState();
    }

    //---------------------------------Threads---------------------------------------------------//

    /**
     * Thread for establishing a bluetooth connection as a client with a remote
     * device.
     */
    private class ConnectThread extends Thread {
        private final BluetoothDevice mmDevice;
        private final BluetoothSocket mmSocket;
        private String mSocketType = "Secure";

        ConnectThread(BluetoothDevice device) {
            Log.d(LOG_TAG, "Connect Thread Created!");
            mmDevice = device;
            BluetoothSocket socket = null;

            Log.d(LOG_TAG, mmDevice.toString());

            // Get a BluetoothSocket for a connection with the
            // given BluetoothDevice
            try {
                socket = mmDevice.createRfcommSocketToServiceRecord(MY_UUID);
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
            synchronized (BluetoothService.this) {
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
                    //mHandler.obtainMessage(Constants.MESSAGE_READ, bytes, -1, buffer)
                            //.sendToTarget();
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
                //mHandler.obtainMessage(Constants.MESSAGE_WRITE, -1, -1, buffer)
                        //.sendToTarget();
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
