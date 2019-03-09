package com.example.android.terminalTexting;

import android.app.IntentService;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Intent;
import android.content.Context;
import android.os.Binder;
import android.os.IBinder;
import android.support.annotation.Nullable;
import android.support.v4.content.LocalBroadcastManager;
import android.telephony.SmsManager;
import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

/**
 * An {@link IntentService} subclass for handling asynchronous task requests in
 * a service on a separate handler thread. The code for this class was heavily
 * influenced by the "Android BluetoothChat Sample" project.
 */
public class BluetoothService extends IntentService {
    // Debugging
    private static final String LOG_TAG = "TermTexting.BtService";

    // Actions the IntentService can perform
    private static final String ACTION_SERVER_CONNECT =
            "com.example.android.terminalTexting.action.SERVER_CONNECT";
    private static final String ACTION_CLIENT_CONNECT =
            "com.example.android.terminalTexting.action.CLIENT_CONNECT";

    // Parameters
    private static final String DEVICE_ADDRESS =
            "com.example.android.terminalTexting.extra.DEVICE_ADDRESS";

    // Unique UUID for this application
    private static final UUID MY_UUID =
            UUID.fromString("56abddf0-d4d2-45c7-9b2b-7837582d436f");

    // Member variables for the service
    private LocalBinder mBinder = new LocalBinder();
    private final BluetoothAdapter mAdapter;
    private ConnectThread mConnectThread;
    private ListenerThread mListenerThread;
    private int mState;
    private int mNewState;
    private BluetoothDevice mDevice;
    private SMSHandler mSMSHandler;

    //-------------------------------Service Start points----------------------------------------//

    /**
     * Starts this service to perform a bluetooth connection as a server. If
     * the service is already performing a task this action will be queued.
     */
    public static void startServerConnect(Context context) {
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

    /**
     * Stop all running threads forked from the service and set their
     * values to null.
     */
    public void stop() {
        if (mListenerThread != null)
            mListenerThread.cancel();
        else if (mConnectThread != null)
            mConnectThread.cancel();
        mListenerThread = null;
        mConnectThread = null;
    }

    /**
     * Used for binding to the service. Needed for whenever an activity, or
     * other service want to send a request to this service.
     * @param intent - contains an Action for the service
     * @return LocalBinder allowing the binding service to access this class
     */
    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        String action = intent.getAction();
        switch (action) {
            case Constants.REQUEST_UPDATE_ACTION:
                // Nothing needed
                break;
            case Constants.WRITE_TO_REMOTE_DEVICE_ACTION:
                String msg = intent.getStringExtra(Constants.MESSAGE_TO_WRITE);
                if (mState == Constants.STATE_CONNECTED) {
                    mListenerThread.write(msg.getBytes());
                }
                break;
            case Constants.STOP_CURRENT_CONNECTION_ACTION:
                stop();
        }
        return mBinder;
    }
//-----------------------------------Process Flow Methods------------------------------------//

    /**
     * Constructor, not really interesting...
     */
    public BluetoothService() {
        super("BluetoothService");
        mAdapter = BluetoothAdapter.getDefaultAdapter();
    }

    @Override
    public void onCreate() {
        super.onCreate();
        mState = Constants.STATE_NONE;
        mNewState = mState;
        mDevice = null;
    }

    @Override
    public void onDestroy() {
        Log.d(LOG_TAG, "stop");

        if (mConnectThread != null) {
            mConnectThread.cancel();
            mConnectThread = null;
        }
        if (mListenerThread != null) {
            mListenerThread.cancel();
            mListenerThread = null;
        }
        mState = Constants.STATE_NONE;

        // Update the UI
        updateUserInterfaceToNewState();

        super.onDestroy();
    }

    private void updateDevice(BluetoothDevice device) {
        mDevice = device;
    }

    public int getState() {
        return mState;
    }

    public String getDeviceName() {
        try {
            return mDevice.getName();
        } catch (NullPointerException e) {
            return null;
        }
    }

    public String getDeviceAddress() {
        try {
            return mDevice.getAddress();
        } catch (NullPointerException e) {
            return null;
        }
    }

    class LocalBinder extends Binder {
        BluetoothService getService() {
            return BluetoothService.this;
        }
    }

    //--------------------------------Action Handling--------------------------------------------//

    @Override
    protected void onHandleIntent(Intent intent) {
        if (intent != null) {
            final String action = intent.getAction();
            switch (action) {
                case ACTION_SERVER_CONNECT:
                    handleActionServerConnect();
                    break;
                case ACTION_CLIENT_CONNECT:
                    final String deviceAddress = intent.getStringExtra(DEVICE_ADDRESS);
                    handleActionClientConnect(deviceAddress);
            }
        }
    }

    /**
     * Handle action Server Connect in the provided background thread.
     */
    private void handleActionServerConnect() {
        // TODO: Handle action server connect
        throw new UnsupportedOperationException("Not yet implemented");
    }

    /**
     * Handle action Client Connect in the provided background thread.
     */
    private void handleActionClientConnect(String deviceAddress) {

        BluetoothDevice device = mAdapter.getRemoteDevice(deviceAddress);

        Log.d(LOG_TAG, "connect to: " + device);
        updateDevice(device);

        // Start the thread to connect with the given device
        mConnectThread = new ConnectThread(device);
        mConnectThread.start();

        // Update the UI
        updateUserInterfaceToConnectedDevice(device.getName(), deviceAddress);
        updateUserInterfaceToNewState();

        // Wait until the connect thread joins (requires the message thread to join too)
        try {
            mConnectThread.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    //--------------------------------User Feedback----------------------------------------------//

    /**
     * Sends the information about the connected device to the user interface so
     * the broadcast receiver can update the display.
     * @param deviceName
     * @param deviceAddress
     */
    private void updateUserInterfaceToConnectedDevice(String deviceName,
                                                      String deviceAddress) {
        Log.d(LOG_TAG, "Updating the User Interface");
        Intent intent = new Intent(Constants.CONNECTED_ACTION)
                .putExtra(Constants.DEVICE_NAME, deviceName)
                .putExtra(Constants.DEVICE_ADDRESS, deviceAddress);
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent);
    }

    private void updateUserInterfaceToFailedConnection() {
        Intent intent = new Intent(Constants.FAILED_CONNECTION_ACTION);
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent);
    }

    private void updateUserInterfaceToLostConnection() {
        Intent intent = new Intent(Constants.LOST_CONNECTION_ACTION);
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent);
    }

    private void updateUserInterfaceToNewState() {
        Log.d(LOG_TAG, "updateUserInterfaceTitle() " + mNewState + " -> " + mState);
        mNewState = mState;

        Intent intent = new Intent(Constants.NEW_STATE_ACTION)
                .putExtra(Constants.BLUETOOTH_STATE, mNewState);
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent);
    }


    //--------------------------------Connection Handling----------------------------------------//

    /**
     * Called when a connection has been made by either the server or client methods.
     * @param socket
     * @param device
     */
    private void connected(BluetoothSocket socket, BluetoothDevice device) {
        Log.d(LOG_TAG, "connected");

        // Cancel the thread that completed the connection
        if (mConnectThread != null) {
            mConnectThread.cancel();
            mConnectThread = null;
        }

        // Cancel any thread currently running a connection
        if (mListenerThread != null) {
            mListenerThread.cancel();
            mListenerThread = null;
        }

        mListenerThread = new ListenerThread(socket);
        mListenerThread.start();

        // Update the UI
        updateUserInterfaceToConnectedDevice(device.getName(), device.getAddress());
        updateUserInterfaceToNewState();
        try {
            mListenerThread.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        stop();
    }

    /**
     * Called when the was an attemped connection that couldn't be completed.
     */
    private void connectionFailed() {
        Log.d(LOG_TAG, "connectionLost()");
        mState = Constants.STATE_NONE;
        updateDevice(null);

        // Update the UI
        updateUserInterfaceToFailedConnection();
        updateUserInterfaceToNewState();
    }

    /**
     * Called when a connection had been made but was lost for some reason.
     */
    private void connectionLost() {
        Log.d(LOG_TAG, "connectionLost()");
        mState = Constants.STATE_NONE;
        updateDevice(null);

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

        ConnectThread(BluetoothDevice device) {
            mmDevice = device;
            BluetoothSocket socket = null;

            // Get a BluetoothSocket for a connection with the
            // given BluetoothDevice
            try {
                socket = mmDevice.createRfcommSocketToServiceRecord(MY_UUID);
                Log.d(LOG_TAG, socket.toString());
            } catch (IOException e) {
                Log.e(LOG_TAG, "Socket create() failed", e);
            }
            mmSocket = socket;
            mState = Constants.STATE_CONNECTING;
        }

        public void run() {
            Log.i(LOG_TAG, "BEGIN mConnectThread");
            setName("ConnectThread");

            // Always cancel discovery because it will slow down a connection
            mAdapter.cancelDiscovery();

            Log.d(LOG_TAG, "attempting to connect");

            // Make a connection to the BluetoothSocket
            try {
                // This is a blocking call and will only return on a
                // successful connection or an exception
                mmSocket.connect();
                Log.d(LOG_TAG, "Connection made!!!");
            } catch (IOException e) {
                Log.e(LOG_TAG, "Unable to connect: " + e.toString());
                try {
                    mmSocket.close();
                } catch (IOException e2) {
                    Log.i(LOG_TAG, "unable to close() " +
                            " socket during connection failure. " + e2.toString());
                }
                connectionFailed();
                return;
            }

            // Reset the ConnectThread because we're done
            synchronized (BluetoothService.this) {
                mConnectThread = null;
            }

            // Start the connected thread
            connected(mmSocket, mmDevice);
        }

        void cancel() {
            try {
                mmSocket.close();
            } catch (IOException e) {
                Log.e(LOG_TAG, "close() of connect socket failed", e);
            }
        }
    }

    /**
     * Thread forked from the connection thread made for listening for
     * incoming messages from the connected device.
     */
    private class ListenerThread extends Thread {
        private final BluetoothSocket mmSocket;
        private final InputStream mmInStream;
        private final OutputStream mmOutStream;

        ListenerThread(BluetoothSocket socket) {
            Log.d(LOG_TAG, "create ConnectedThread");
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

            // Set up the broadcast receiver to listen for incoming messages
            mSMSHandler = new SMSHandler(BluetoothService.this) {
                @Override
                public void callback(MessagePackage msg) {
                    ListenerThread.this.write(msg.getBytes());
                }
            };
        }

        public void run() {
            Log.i(LOG_TAG, "BEGIN mListenerThread");
            byte[] buffer = new byte[1024];
            int bytes;
            SMSHandler.MessagePackage msgPack;

            // Keep listening to the InputStream while connected
            while (mState == Constants.STATE_CONNECTED) {
                try {
                    bytes = mmInStream.read(buffer);
                    if (bytes <= 13) {
                        throw new IOException("Incoming message was too short.");
                    }
                } catch (IOException e) {
                    Log.i(LOG_TAG, "disconnected\n" + e.toString());
                    try {
                        mmSocket.close();
                    } catch (IOException e2) {
                        Log.i(LOG_TAG, "unable to close() " +
                                " socket during connection failure. " + e2.toString());
                    }
                    connectionLost();
                    break;
                }
                Log.d(LOG_TAG, "buffer: " + new String(buffer));
                try {
                    msgPack = new SMSHandler.MessagePackage(buffer);
                } catch (Exception e) {
                    Log.i(LOG_TAG, "disconnecting due to read error\n" + e.toString());
                    try {
                        mmSocket.close();
                    } catch (IOException e2) {
                        Log.i(LOG_TAG, "unable to close() " +
                                " socket during connection failure. " + e2.toString());
                    }
                    connectionLost();
                    break;
                }
                SmsManager smsManager = SmsManager.getDefault();
                smsManager.sendTextMessage(msgPack.number, null, msgPack.message,
                        null, null);
            }
            Log.d(LOG_TAG, "ListenerThread is finishing");
            mSMSHandler.close();
        }

        void write(byte[] buffer) {
            try {
                mmOutStream.write(buffer);
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
