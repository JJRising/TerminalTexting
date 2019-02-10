package com.example.android.terminalTexting;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.support.annotation.Nullable;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends AppCompatActivity {

    // Permission request codes
    private static final int MY_PERMISSIONS_REQUEST_SEND_SMS = 1;
    private static final int MY_PERMISSIONS_REQUEST_RECEIVE_SMS = 2;

    // Intent request codes
    private static final int REQUEST_CONNECT_DEVICE_SECURE = 1;
    private static final int REQUEST_CONNECT_DEVICE_UNSECURED = 2;
    private static final int REQUEST_ENABLE_BT = 3;

    // UI elements
    private TextView mStatusText;
    private TextView mLogText;
    private Button mConnectButton;

    private BluetoothAdapter mBtAdapter;
    private BluetoothConnectionService mBTS;

    private int connectionState = Constants.STATE_NONE;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        mBtAdapter = BluetoothAdapter.getDefaultAdapter();
        mBTS = new BluetoothConnectionService(mHandler);

        // Get the UI elements
        mConnectButton = findViewById(R.id.connect_button);
        mStatusText = findViewById(R.id.status_text);
        updateStatus(Constants.STATE_NONE);
        mLogText = findViewById(R.id.comm_log);

        textLog("Main activity created");
    }

    @Override
    protected void onStart() {
        super.onStart();
        // If BT is not on, request that it be enabled.
        // setupChat() will then be called during onActivityResult
        if (!mBtAdapter.isEnabled()) {
            Intent enableIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            startActivityForResult(enableIntent, REQUEST_ENABLE_BT);
            // Otherwise, setup the chat session
        }
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

    private void updateStatus(int newStatus) {
        String statusTitle = getString(R.string.status);
        String statusTxt;
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
        connectionState = newStatus;
        String displayTxt = statusTitle + " " + statusTxt;
        mStatusText.setText(displayTxt);
    }

    public void connectNewDevice(View view) {
        if (connectionState == Constants.STATE_NONE) {
            Intent intent = new Intent(MainActivity.this, DeviceListActivity.class);
            startActivityForResult(intent, REQUEST_CONNECT_DEVICE_SECURE);
        } else if (connectionState == Constants.STATE_CONNECTED) {
            mBTS.stop();
        }
    }

    public void sendTest(View view) {
        String testString = "Test string to be sent.";
        mBTS.write(testString.getBytes());
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        switch (requestCode) {
            case REQUEST_CONNECT_DEVICE_SECURE:
                if (resultCode == Activity.RESULT_OK) {
                    connectDevice(data, true);
                }
                break;
            case REQUEST_CONNECT_DEVICE_UNSECURED:
                if (resultCode == Activity.RESULT_OK) {
                    connectDevice(data, false);
                }
        }
    }

    private void connectDevice(Intent data, boolean secure) {
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
        BluetoothDevice device = mBtAdapter.getRemoteDevice(address);

        // Log the action
        String txt = "attempting to connect to:\n" + deviceName + "\n" + address;
        textLog(txt);

        int MY_PERMISSIONS_REQUEST_BLUETOOTH = 1;
        ActivityCompat.requestPermissions(this,
                new String[]{Manifest.permission.BLUETOOTH},
                MY_PERMISSIONS_REQUEST_BLUETOOTH);

        mBTS.connect(device, secure);
    }

    private void textLog(String txt) {
        String mytxt = "\n" + txt;
        mLogText.append(mytxt);
    }

    @SuppressLint("HandlerLeak")
    private final Handler mHandler = new Handler() {
        @Override
        public void handleMessage(Message msg) {
            switch (msg.what) {
                case Constants.MESSAGE_STATE_CHANGE:
                    updateStatus(msg.arg1);
                    break;
                case Constants.MESSAGE_READ:
                    break;
                case Constants.MESSAGE_WRITE:
                    break;
                case Constants.MESSAGE_DEVICE_NAME:
                    String deviceName = msg.getData().getString(Constants.DEVICE_NAME);
                    Toast.makeText(MainActivity.this, "Connected to " + deviceName,
                            Toast.LENGTH_SHORT).show();
                    break;
                case Constants.MESSAGE_TOAST:
                    Toast.makeText(MainActivity.this,
                            msg.getData().getString(Constants.TOAST), Toast.LENGTH_SHORT).show();
                    break;
                case Constants.MESSAGE_TEXTLOG:
                    textLog(msg.getData().getString(Constants.TEXT));
                    break;
            }
        }
    };

    public void switchMessagingApp(View view) {
    }
}
