package org.libusb;
import android.content.Context;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.util.SparseArray;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Vector;
public class LibUsbManager {
    public static final String TAG = "LibUsb";
    public static SparseArray<UsbDeviceConnection> m_connectionMap = new SparseArray<>();
    public static Context m_context = null;
    public static Vector<DeviceDesc> m_descVector = new Vector<>();
    public static int m_hasPermitUsbDevice = 0;
    protected static class DeviceDesc {
        public final byte[] descriptors;
        public final int deviceId;
        public DeviceDesc(int i, byte[] bArr) {
            this.deviceId = i;
            this.descriptors = bArr;
        }
    }
    static {
        System.loadLibrary("usb");
    }
    public static void closeDevice(int i) {
        UsbDeviceConnection usbDeviceConnection;
        if (m_context == null || (usbDeviceConnection = m_connectionMap.get(i)) == null) {
            return;
        }
        usbDeviceConnection.close();
        m_connectionMap.remove(i);
    }
    public static UsbDevice findDevice(int i) {
        for (UsbDevice usbDevice : ((UsbManager) m_context.getSystemService("usb")).getDeviceList().values()) {
            if (usbDevice.getDeviceId() == i) {
                return usbDevice;
            }
        }
        return null;
    }
    public static DeviceDesc[] getDeviceArray() {
        Context context = m_context;
        if (context != null) {
            UsbManager usbManager = (UsbManager) context.getSystemService("usb");
            HashMap<String, UsbDevice> deviceList = usbManager.getDeviceList();
            new Vector();
            int i = 0;
            Iterator<UsbDevice> it = deviceList.values().iterator();
            while (it.hasNext()) {
                if (usbManager.hasPermission(it.next())) {
                    i++;
                }
            }
            if (i != m_hasPermitUsbDevice) {
                m_hasPermitUsbDevice = i;
                m_descVector.clear();
                for (UsbDevice usbDevice : deviceList.values()) {
                    if (usbManager.hasPermission(usbDevice) && (usbDevice.getVendorId() == 4415 || usbDevice.getVendorId() == 8122)) {
                        UsbDeviceConnection openDevice = usbManager.openDevice(usbDevice);
                        if (openDevice != null) {
                            byte[] rawDescriptors = openDevice.getRawDescriptors();
                            openDevice.close();
                            m_descVector.add(new DeviceDesc(usbDevice.getDeviceId(), rawDescriptors));
                        }
                    }
                }
            }
        }
        Vector<DeviceDesc> vector = m_descVector;
        return (DeviceDesc[]) vector.toArray(new DeviceDesc[vector.size()]);
    }
    public static void logPrintError(String str) {
    }
    public static void logPrintWarning(String str) {
    }
    public static int openDevice(int i) {
        UsbDevice findDevice;
        UsbDeviceConnection openDevice;
        if (m_context != null && (findDevice = findDevice(i)) != null) {
            UsbManager usbManager = (UsbManager) m_context.getSystemService("usb");
            if (usbManager.hasPermission(findDevice) && (openDevice = usbManager.openDevice(findDevice)) != null) {
                int fileDescriptor = openDevice.getFileDescriptor();
                m_connectionMap.put(findDevice.getDeviceId(), openDevice);
                return fileDescriptor;
            }
        }
        return -1;
    }
    public static void setContext(Context context) {
        m_context = context;
    }
}
