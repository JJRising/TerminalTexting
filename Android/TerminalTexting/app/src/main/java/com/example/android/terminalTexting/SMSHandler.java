package com.example.android.terminalTexting;

import android.annotation.TargetApi;
import android.content.BroadcastReceiver;
import android.content.ContentResolver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.ContactsContract;
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
            byte[] m = new byte[4];
            in.read(m, 13 + (int) contactLength[0], 4);
            int messageLength = m[3]*128^3 + m[2]*128^2 + m[1]*128 + m[0];
            // Read the rest of the message.
            byte[] myMessageBytes = new byte[messageLength];
            in.read(myMessageBytes, 13 + (int) contactLength[0] + 4, messageLength);
            message = new String(myMessageBytes);
        }

        byte[] getBytes() {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte type = (byte) 255;
            out.write(type);
            out.write(number.getBytes(), 0, 12);
            out.write(contactName.length());
            out.write(contactName.getBytes(), 0, contactName.length());
            Log.d("TERMTEXT.getBytes", Integer.toString(message.length()));
            int mLength = message.length();
            for (int i = 0; i < 4; i++) {
                Log.d("TERMTEXT.getBytes", Integer.toString(mLength%128));
                out.write(mLength%128);
                mLength/=128;
            }
            out.write(message.getBytes(), 0, message.length());
            return out.toByteArray();
        }
    }

    public void close() {
        receiverContext.unregisterReceiver(mSmsReceiver);
    }

    public abstract void callback(MessagePackage msg);

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
            String format = Objects.requireNonNull(bundle).getString("format");
            // Retrieve the SMS message received.
            Object[] pdus = (Object[]) bundle.get(pdu_type);
            if (pdus != null) {
                // Check the Android version.
                boolean isVersionM = (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M);
                // Fill msgs array.
                SmsMessage[] msgs;
                msgs = new SmsMessage[pdus.length];
                String number, contactName = "Unknown Number";
                StringBuilder fullMessage = new StringBuilder();
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
                    fullMessage.append(msgs[i].getMessageBody());

                    // Pass strMessage to the callback method
                }
                number = msgs[0].getOriginatingAddress();
                // TODO: contactName
                // Look up contact name
                Uri uri = Uri.withAppendedPath(ContactsContract.PhoneLookup.CONTENT_FILTER_URI,
                        Uri.encode(number));
                ContentResolver resolver = receiverContext.getContentResolver();
                Log.d(LOG_TAG, "Hi there!");
                try (Cursor cursor = resolver.query(uri, new String[]{
                                ContactsContract.PhoneLookup.DISPLAY_NAME},
                        null, null, null)) {
                    Log.d(LOG_TAG, cursor.toString());
                    if (cursor != null && cursor.getCount() > 0) {
                        cursor.moveToFirst();
                        Log.d(LOG_TAG, "fingers crossed");
                        contactName = cursor.getString(
                                cursor.getColumnIndex(ContactsContract.Data.DISPLAY_NAME));
                        Log.d(LOG_TAG, contactName);
                    }
                } catch (Exception e) {

                    contactName = "Unknown Number";
                }
                Log.d(LOG_TAG, fullMessage.toString());
                MessagePackage msgPackage = new MessagePackage(
                        number,
                        contactName,
                        fullMessage.toString());

                callback(msgPackage);
            }
        }
    }
}
