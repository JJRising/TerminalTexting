package com.example.android.terminalTexting;

import android.annotation.TargetApi;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.Bundle;
import android.telephony.SmsManager;
import android.telephony.SmsMessage;
import android.util.Log;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.util.Objects;

abstract class SMSHandler {
    private final String LOG_TAG = "SMSHandler";

    private SmsReceiver mSmsReceiver;
    private Context receiverContext;

    SMSHandler(Context context) {
        receiverContext = context;
        IntentFilter smsReceivedFilter = new IntentFilter();
        smsReceivedFilter.addAction("android.provider.Telephony.SMS_RECEIVED");
        mSmsReceiver = new SmsReceiver();
        receiverContext.registerReceiver(mSmsReceiver, smsReceivedFilter);
    }

    static class MessagePackage {
        String number;
        String contactName;
        String message;

        MessagePackage(String number, String contactName, String message) {
            if (number.length() != 12) {
                if (number.length() == 10) {
                    this.number = "+1" + number;
                }
            } else {
                this.number = number;
            }
            this.contactName = contactName;
            this.message = message;
        }

        MessagePackage(byte[] bytes) {
            ByteArrayInputStream in = new ByteArrayInputStream(bytes);
            // Read the number
            byte[] myNumberBytes = new byte[12];
            in.read(myNumberBytes, 0, 12);
            number = new String(myNumberBytes);
            // Read how long the contact name is
            byte[] contactLength = new byte[1];
            in.read(contactLength, 12, 1);
            // Read the contact name.
            byte[] myContactNameBytes = new byte[(int) contactLength[0]];
            in.read(myContactNameBytes, 13, (int) contactLength[0]);
            contactName = new String(myContactNameBytes);
            // Read how long the message is.
            byte[] messageLength = new byte[1];
            in.read(messageLength, 13 + (int) contactLength[0], 1);
            // Read the rest of the message.
            byte[] myMessageBytes = new byte[(int) messageLength[1]];
            in.read(myMessageBytes, 13 + (int) contactLength[0], (int) messageLength[1]);
            message = new String(myMessageBytes);
        }

        byte[] getBytes() {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            out.write(number.getBytes(), 0, 12);
            out.write(contactName.length());
            out.write(contactName.getBytes(), 0, contactName.length());
            out.write(message.length());
            out.write(message.getBytes(), 0, message.length());
            return out.toByteArray();
        }
    }

    public void close() {
        receiverContext.unregisterReceiver(mSmsReceiver);
    }

    public abstract void callback(String msg);

    public void sendText(String phoneNumber, String smsMessage) {
        SmsManager smsManager = SmsManager.getDefault();
        smsManager.sendTextMessage(phoneNumber, null, smsMessage,
                null, null);
    }

    public class SmsReceiver extends BroadcastReceiver {
        public static final String pdu_type = "pdus";

        @TargetApi(Build.VERSION_CODES.M)
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d(LOG_TAG, "Received Broadcast!");
            // Get the SMS message.
            Bundle bundle = intent.getExtras();
            SmsMessage[] msgs;
            StringBuilder strMessage = new StringBuilder();
            String format = Objects.requireNonNull(bundle).getString("format");
            // Retrieve the SMS message received.
            Object[] pdus = (Object[]) bundle.get(pdu_type);
            if (pdus != null) {
                // Check the Android version.
                boolean isVersionM = (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M);
                // Fill msgs array.
                msgs = new SmsMessage[pdus.length];
                for (int i = 0; i < msgs.length; i++) {
                    // Check Android version and use appropriate createFromPdu.
                    if (isVersionM) {
                        // If Android version M or newer:
                        msgs[i] =
                                SmsMessage.createFromPdu((byte[]) pdus[i], format);
                    } else {
                        // If Android version L or older:
                        msgs[i] = SmsMessage.createFromPdu((byte[]) pdus[i]);
                    }
                    // Build the message to show.
                    strMessage.append("SMS from ")
                            .append(msgs[i].getOriginatingAddress())
                            .append(" :")
                            .append(msgs[i].getMessageBody()).append("\n");

                    // Pass strMessage to the callback method
                    callback(strMessage.toString());
                }
            }
        }
    }
}
