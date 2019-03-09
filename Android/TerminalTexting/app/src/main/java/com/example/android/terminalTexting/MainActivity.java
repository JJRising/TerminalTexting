package com.example.android.terminalTexting;

import android.Manifest;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.support.annotation.Nullable;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.util.Log;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends AppCompatActivity {
    private static final String LOG_TAG = "MainActivity";

    // Permission request codes
    private static final int MY_PERMISSIONS_REQUEST_EVERYTHING = 5;

    // Intent request codes
    private static final int REQUEST_CONNECT_DEVICE = 1;
    private static final int REQUEST_ENABLE_BT = 2;

    private BluetoothStateReceiver mBluetoothStateReceiver;
    private int mBluetoothState;

    // UI elements
    private TextView mStatusText;
    private TextView mDeviceNameText;
    private TextView mDeviceAddressText;
    private TextView mLogText;
    private Button mConnectButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        // IntentFilter for the BluetoothStateReceiver
        IntentFilter bluetoothStatusFilter = new IntentFilter();
        bluetoothStatusFilter.addAction(Constants.CONNECTED_ACTION);
        bluetoothStatusFilter.addAction(Constants.FAILED_CONNECTION_ACTION);
        bluetoothStatusFilter.addAction(Constants.LOST_CONNECTION_ACTION);
        bluetoothStatusFilter.addAction(Constants.NEW_STATE_ACTION);
        mBluetoothStateReceiver = new BluetoothStateReceiver();
        LocalBroadcastManager.getInstance(this).registerReceiver(
                mBluetoothStateReceiver,
                bluetoothStatusFilter);

        // Get the UI elements
        mConnectButton = findViewById(R.id.connect_button);
        mStatusText = findViewById(R.id.status_text);
        mDeviceNameText = findViewById(R.id.device_name);
        mDeviceAddressText = findViewById(R.id.device_id);
        updateStatus(Constants.STATE_NONE);
        mLogText = findViewById(R.id.comm_log);

        // Required Permissions
        ActivityCompat.requestPermissions(this,
                new String[]{Manifest.permission.READ_CONTACTS,
                             Manifest.permission.SEND_SMS,
                             Manifest.permission.RECEIVE_SMS,
                             Manifest.permission.ACCESS_COARSE_LOCATION},
                MY_PERMISSIONS_REQUEST_EVERYTHING);

        // Try to bind to a active BluetoothService
        Intent intent = new Intent(this, BluetoothService.class);
        intent.setAction(Constants.REQUEST_UPDATE_ACTION);
        requestUpdateConnectionIsBound = bindService(intent, requestUpdateConnection, 0);
        Log.d(LOG_TAG, "IsBound: " + requestUpdateConnectionIsBound.toString());

        textLog("Main activity created");
    }

    @Override
    protected void onDestroy() {
        if (requestUpdateConnectionIsBound)
            unbindService(requestUpdateConnection);
        if (basicServiceConnectionIsBound)
            unbindService(basicServiceConnection);
        LocalBroadcastManager.getInstance(this).unregisterReceiver(mBluetoothStateReceiver);
        super.onDestroy();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    /**
     * Changes the Status text at the top of the activity depending on the
     * bluetooth Services state.
     * @param newStatus - equals a value from the Constants interface.
     */
    void updateStatus(int newStatus) {
        String statusTitle = getString(R.string.status);
        String statusTxt;
        mBluetoothState = newStatus;
        switch (newStatus) {
            case Constants.STATE_NONE:
                statusTxt = getString(R.string.state_none);
                mConnectButton.setEnabled(true);
                mConnectButton.setText(R.string.connect_button_connect);
                break;
            case Constants.STATE_CONNECTING:
                statusTxt = getString(R.string.state_connecting);
                mConnectButton.setEnabled(false);
                break;
            case Constants.STATE_CONNECTED:
                statusTxt = getString(R.string.state_connected);
                mConnectButton.setEnabled(true);
                mConnectButton.setText(R.string.connect_button_disconnect);
                break;
            default:
                statusTxt = getString(R.string.status_debug);
                break;
        }
        String displayTxt = statusTitle + " " + statusTxt;
        mStatusText.setText(displayTxt);
    }

    /**
     * Changes the text at the top of the activity
     * @param name - bluetooth name of the connected device
     * @param address - bluetooth address of the connected device
     */
    void updateConnectedDevice(String name, String address) {
        String nameTitle = getString(R.string.device_name);
        String addressTitle = getString(R.string.device_id);
        String displayName = nameTitle + " " + name;
        String displayAddress = addressTitle + " " + address;
        mDeviceNameText.setText(displayName);
        mDeviceAddressText.setText(displayAddress);
    }

    /**
     * OnClick function for the Connect button.
     *
     * @param view: The view element for the connect button
     */
    public void connectNewDevice(View view) {
        if (mBluetoothState == Constants.STATE_NONE) {
            Intent intent = new Intent(this, DeviceListActivity.class);
            startActivityForResult(intent, REQUEST_CONNECT_DEVICE);
        } else if (mBluetoothState == Constants.STATE_CONNECTED) {
            disconnectDevice();
        }
    }

    /**
     * OnClick function for the Send Test button
     *
     * @param view: The view element for the send test button
     */
    public void sendTest(View view) {
        String testString = "Test string to be sent.";

        Intent intent = new Intent(this, BluetoothService.class);
        intent.setAction(Constants.WRITE_TO_REMOTE_DEVICE_ACTION);
        intent.putExtra(Constants.MESSAGE_TO_WRITE, testString);
        basicServiceConnectionIsBound = bindService(intent, basicServiceConnection, 0);
    }

    public void switchMessagingApp(View view) {
        // TODO: Remove, not needed
    }

    /**
     * Result from the DeviceListActivity
     * @param requestCode - should always be REQUEST_CONNECT_DEVICE
     * @param resultCode - from the DeviceListActivity
     * @param data - Intent containing the address of the device to connect to.
     */
    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        switch (requestCode) {
            case REQUEST_CONNECT_DEVICE:
                if (resultCode == Activity.RESULT_OK) {
                    connectDevice(data);
                }
                break;
        }
    }

    /**
     * Launches the DeviceListActivity to get a device to connect to and starts
     * a bluetooth service to connect to that device.
     * @param data
     */
    private void connectDevice(Intent data) {
        // Display Toast message that you are trying to connect
        String deviceName;
        try {
            deviceName = data.getExtras().getString(DeviceListActivity.EXTRA_DEVICE_NAME);
        } catch (Exception e) {
            deviceName = "Device Name Unavailable";
        }
        Toast.makeText(this, "Attempting to connect to " + deviceName,
                Toast.LENGTH_SHORT).show();
        // Get the MAC address
        String address = data.getExtras().getString(DeviceListActivity.EXTRA_DEVICE_ADDRESS);

        // Log the action
        String txt = "attempting to connect to:\n" + deviceName + "\n" + address;
        textLog(txt);

        BluetoothService.startClientConnect(this, address);
    }

    /**
     * Sends an intent to the bluetoothService to disconnect the currently
     * connected device.
     */
    private void disconnectDevice() {
        Intent intent = new Intent(this, BluetoothService.class);
        intent.setAction(Constants.STOP_CURRENT_CONNECTION_ACTION);
        basicServiceConnectionIsBound = bindService(intent, basicServiceConnection, 0);
    }

    /**
     * Printing to the scolling text window at the bottom of the activity.
     * @param txt - text to be printed
     */
    void textLog(String txt) {
        String my_txt = "\n" + txt;
        mLogText.append(my_txt);
    }

    /**
     * Binding to the BluetoothService for requesting and receiving the current
     * bluetooth state. Is needed for when loading the activity while the
     * service is running.
     */
    private Boolean requestUpdateConnectionIsBound = false;
    private ServiceConnection requestUpdateConnection = new ServiceConnection() {
        // Called when the connection with the service is established
        @Override
        public void onServiceConnected(ComponentName name, IBinder service) {
            Log.d(LOG_TAG, service.toString());
            BluetoothService.LocalBinder binder = (BluetoothService.LocalBinder) service;
            BluetoothService btService = binder.getService();
            int state = btService.getState();
            String deviceName = btService.getDeviceName();
            String deviceAddress = btService.getDeviceAddress();
            updateStatus(state);
            updateConnectedDevice(deviceName, deviceAddress);
            unbindService(this);
            requestUpdateConnectionIsBound = false;
        }

        // Called when the connection with the service disconnects unexpectedly
        @Override
        public void onServiceDisconnected(ComponentName name) {
            updateStatus(Constants.STATE_NONE);
            updateConnectedDevice("", "");
        }
    };

    /**
     * Binding to the BluetoothService for sending basic instructions such as disconnect.
     */
    private Boolean basicServiceConnectionIsBound = false;
    private ServiceConnection basicServiceConnection = new ServiceConnection() {
        @Override
        public void onServiceConnected(ComponentName name, IBinder service) {
            unbindService(this);
            basicServiceConnectionIsBound = false;
        }

        @Override
        public void onServiceDisconnected(ComponentName name) {
        }
    };

    /**
     * Receives a broadcast sent from the BluetoothService indicating state transitions.
     */
    public class BluetoothStateReceiver extends BroadcastReceiver {
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d("BtStateReceiver", context.toString());
            switch (intent.getAction()) {
                case Constants.CONNECTED_ACTION:
                    String name = intent.getExtras().getString(Constants.DEVICE_NAME);
                    String address = intent.getExtras().getString(Constants.DEVICE_ADDRESS);
                    updateConnectedDevice(name, address);
                    break;
                case Constants.FAILED_CONNECTION_ACTION:
                    textLog(getString(R.string.failed_connection));
                    updateConnectedDevice("", "");
                    break;
                case Constants.LOST_CONNECTION_ACTION:
                    textLog(getString(R.string.lost_connection));
                    updateConnectedDevice("", "");
                    break;
                case Constants.NEW_STATE_ACTION:
                    int state = intent.getExtras().getInt(Constants.BLUETOOTH_STATE);
                    updateStatus(state);
                    break;
                default:
                    break;
            }
        }
    }
}
