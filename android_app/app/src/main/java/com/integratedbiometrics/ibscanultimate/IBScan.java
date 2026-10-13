package com.integratedbiometrics.ibscanultimate;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbManager;
import com.integratedbiometrics.ibscanultimate.IBScanException;
import org.libusb.LibUsbManager;
public class IBScan {
    public static final String ACTION_USB_PERMISSION = "ibscan.USB_PERMISSION";
    public static int METHOD_STACK_INDEX = 0;
    public static final int PID_COLUMBO = 4352;
    public static final int PID_COLUMBO_REV1 = 4353;
    public static final int PID_CURVE = 4100;
    public static final int PID_DANNO = 5632;
    public static final int PID_FIVE0 = 5376;
    public static final int PID_FIVE0_DERMALOG = 52;
    public static final int PID_FIVE0_REV1 = 5377;
    public static final int PID_HOLMES = 4608;
    public static final int PID_KOJAK = 4864;
    public static final int PID_KOJAK_DERMALOG = 54;
    public static final int PID_KOJAK_LOCK = 6656;
    public static final int PID_KOJAK_REV1 = 4865;
    public static final int PID_SHERLOCK = 4112;
    public static final int PID_SHERLOCK_AUO = 4113;
    public static final int PID_WATSON = 4101;
    public static final int PID_WATSON_MINI = 4128;
    public static final int PID_WATSON_MINI_REV1 = 4129;
    public static final int PID_WATSON_REV1 = 4102;
    public static final int VID_DERMALOG = 8122;
    public static final int VID_IB = 4415;
    public static IBScan m_instance;
    public IBScanListener m_listener = null;
    public Context m_context = null;
    public final BroadcastReceiver m_usbReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (action.equals("android.hardware.usb.action.USB_DEVICE_ATTACHED")) {
                UsbDevice usbDevice = (UsbDevice) intent.getParcelableExtra("device");
                if (usbDevice == null || !IBScan.isScanDevice(usbDevice)) {
                    return;
                }
                IBScan.callbackScanDeviceAttached(usbDevice.getDeviceId());
                return;
            }
            if (action.equals("android.hardware.usb.action.USB_DEVICE_DETACHED")) {
                UsbDevice usbDevice2 = (UsbDevice) intent.getParcelableExtra("device");
                if (usbDevice2 == null || !IBScan.isScanDevice(usbDevice2)) {
                    return;
                }
                IBScan.callbackScanDeviceDetached(usbDevice2.getDeviceId());
                return;
            }
            if (action.equals(IBScan.ACTION_USB_PERMISSION) && intent.hasExtra("permission")) {
                boolean booleanExtra = intent.getBooleanExtra("permission", false);
                UsbDevice usbDevice3 = (UsbDevice) intent.getParcelableExtra("device");
                if (usbDevice3 == null || !IBScan.isScanDevice(usbDevice3)) {
                    return;
                }
                IBScan.callbackScanDevicePermissionGranted(usbDevice3.getDeviceId(), booleanExtra);
            }
        }
    };
    public static final class DeviceDesc {
        public final String customerString;
        public final String devRevision;
        public final int deviceId;
        public final String fwVersion;
        public final String interfaceType;
        public final boolean isLocked;
        public final boolean isOpened;
        public final String productName;
        public final String serialNumber;
        public DeviceDesc(String str, String str2, String str3, String str4, String str5, boolean z, int i, boolean z2, String str6) {
            this.serialNumber = str;
            this.productName = str2;
            this.interfaceType = str3;
            this.fwVersion = str4;
            this.devRevision = str5;
            this.isOpened = z;
            this.deviceId = i;
            this.isLocked = z2;
            this.customerString = str6;
        }
        public final String toString() {
            StringBuilder sb = new StringBuilder("Serial Number: ");
            sb.append(this.serialNumber);
            sb.append("\nProduct Name: ");
            sb.append(this.productName);
            sb.append("\nInterface Type: ");
            sb.append(this.interfaceType);
            sb.append("\nFirmware Version: ");
            sb.append(this.fwVersion);
            sb.append("\nDevice Revision: ");
            sb.append(this.devRevision);
            sb.append("\nDevice Opened: ");
            sb.append(this.isOpened);
            sb.append("\nDevice Locked: ");
            sb.append(this.isLocked);
            sb.append("\nCustomer String: ");
            sb.append(this.customerString);
            sb.append("\nDevice ID: ");
            return sb.append(this.deviceId).append("\n").toString();
        }
    }
    public enum HashType {
        SHA256(0),
        Reserved(1);
        public final int code;
        HashType(int i) {
            this.code = i;
        }
        public static HashType fromCode(int i) {
            for (HashType hashType : values()) {
                if (hashType.code == i) {
                    return hashType;
                }
            }
            return null;
        }
        public final int toCode() {
            return this.code;
        }
    }
    protected static final class NativeError {
        public int code = 0;
    }
    public static final class SdkVersion {
        public final String file;
        public final String product;
        public SdkVersion(String str, String str2) {
            this.product = str;
            this.file = str2;
        }
        public final String toString() {
            StringBuilder sb = new StringBuilder("Product: ");
            sb.append(this.product);
            sb.append("\nFile: ");
            return sb.append(this.file).append("\n").toString();
        }
    }
    static {
        int i = 0;
        for (StackTraceElement stackTraceElement : Thread.currentThread().getStackTrace()) {
            i++;
            if (stackTraceElement.getClassName().equals(IBScan.class.getName())) {
                break;
            }
        }
        METHOD_STACK_INDEX = i;
        System.loadLibrary("usb");
        System.loadLibrary("ibscanultimate");
        System.loadLibrary("ibscanultimatejni");
    }
    public IBScan() {
        initNative();
    }
    public static void callbackScanDeviceAttached(int i) {
        IBScanListener iBScanListener;
        IBScan iBScan = m_instance;
        if (iBScan == null || (iBScanListener = iBScan.m_listener) == null) {
            return;
        }
        iBScanListener.scanDeviceAttached(i);
    }
    public static void callbackScanDeviceCountChanged(int i) {
        IBScanListener iBScanListener;
        IBScan iBScan = m_instance;
        if (iBScan == null || (iBScanListener = iBScan.m_listener) == null) {
            return;
        }
        iBScanListener.scanDeviceCountChanged(i);
    }
    public static void callbackScanDeviceDetached(int i) {
        IBScanListener iBScanListener;
        IBScan iBScan = m_instance;
        if (iBScan == null || (iBScanListener = iBScan.m_listener) == null) {
            return;
        }
        iBScanListener.scanDeviceDetached(i);
    }
    public static void callbackScanDeviceInitProgress(int i, int i2) {
        IBScanListener iBScanListener;
        IBScan iBScan = m_instance;
        if (iBScan == null || (iBScanListener = iBScan.m_listener) == null) {
            return;
        }
        iBScanListener.scanDeviceInitProgress(i, i2);
    }
    public static void callbackScanDeviceOpenComplete(int i, IBScanDevice iBScanDevice, int i2) {
        IBScan iBScan = m_instance;
        if (iBScan == null || iBScan.m_listener == null) {
            return;
        }
        iBScan.m_listener.scanDeviceOpenComplete(i, iBScanDevice, new IBScanException(IBScanException.Type.fromCode(i2)));
    }
    public static void callbackScanDevicePermissionGranted(int i, boolean z) {
        IBScanListener iBScanListener;
        IBScan iBScan = m_instance;
        if (iBScan == null || (iBScanListener = iBScan.m_listener) == null) {
            return;
        }
        iBScanListener.scanDevicePermissionGranted(i, z);
    }
    private native void enableTraceLogNative(boolean z, NativeError nativeError);
    private UsbDevice findDevice(int i) {
        Context context = this.m_context;
        if (context != null) {
            for (UsbDevice usbDevice : ((UsbManager) context.getSystemService("usb")).getDeviceList().values()) {
                if (usbDevice.getDeviceId() == i) {
                    return usbDevice;
                }
            }
        }
        return null;
    }
    private native int getDeviceCountNative(NativeError nativeError);
    private native DeviceDesc getDeviceDescNative(int i, NativeError nativeError);
    private native String getErrorStringNative(int i, NativeError nativeError);
    private native int getInitProgressNative(int i, NativeError nativeError);
    public static IBScan getInstance(Context context) {
        if (m_instance == null) {
            m_instance = new IBScan();
        }
        m_instance.setContext(context);
        return m_instance;
    }
    public static String getMethodName() {
        StackTraceElement[] stackTrace = Thread.currentThread().getStackTrace();
        int length = stackTrace.length;
        int i = METHOD_STACK_INDEX;
        return length > i ? stackTrace[i].getMethodName() : "?";
    }
    private native String getRequiredSDKVersionNative(int i, NativeError nativeError);
    private native SdkVersion getSdkVersionNative(NativeError nativeError);
    public static void handleError(NativeError nativeError) throws IBScanException {
        int i = nativeError.code;
        if (i != 0) {
            IBScanException.Type fromCode = IBScanException.Type.fromCode(i);
            if (fromCode == null) {
                StringBuilder sb = new StringBuilder();
                sb.append(getMethodName());
                sb.append(": unrecognized error code(");
                sb.append(nativeError.code).append(") returned from native code");
                fromCode = IBScanException.Type.COMMAND_FAILED;
            }
            throw new IBScanException(fromCode);
        }
    }
    private native void initNative();
    public static boolean isScanDevice(UsbDevice usbDevice) {
        int vendorId = usbDevice.getVendorId();
        if (vendorId != 4415 && vendorId != 8122) {
            return false;
        }
        int[] iArr = {PID_CURVE, PID_WATSON, PID_WATSON_REV1, PID_SHERLOCK, PID_SHERLOCK_AUO, PID_WATSON_MINI, PID_WATSON_MINI_REV1, PID_COLUMBO, PID_COLUMBO_REV1, PID_KOJAK, PID_KOJAK_REV1, PID_HOLMES, PID_FIVE0, PID_FIVE0_REV1, 52, PID_DANNO, PID_KOJAK_LOCK, 54};
        int productId = usbDevice.getProductId();
        for (int i = 0; i < 18; i++) {
            if (iArr[i] == productId) {
                return true;
            }
        }
        return false;
    }
    public static void logPrintError(String str) {
    }
    public static void logPrintWarning(String str) {
    }
    private native void openDeviceAsyncExNative(int i, String str, NativeError nativeError);
    private native void openDeviceAsyncNative(int i, NativeError nativeError);
    private native IBScanDevice openDeviceExNative(int i, String str, NativeError nativeError);
    private native IBScanDevice openDeviceNative(int i, NativeError nativeError);
    private native void setCustomerKeyNative(int i, int i2, String str, NativeError nativeError);
    private native int unloadLibraryNative(NativeError nativeError);
    private native void updateUsbPermissionNative();
    public void enableTraceLog(boolean z) throws IBScanException {
        NativeError nativeError = new NativeError();
        enableTraceLogNative(z, nativeError);
        handleError(nativeError);
    }
    public int getDeviceCount() throws IBScanException {
        NativeError nativeError = new NativeError();
        int deviceCountNative = getDeviceCountNative(nativeError);
        handleError(nativeError);
        return deviceCountNative;
    }
    public DeviceDesc getDeviceDescription(int i) throws IBScanException {
        NativeError nativeError = new NativeError();
        DeviceDesc deviceDescNative = getDeviceDescNative(i, nativeError);
        handleError(nativeError);
        return deviceDescNative;
    }
    public String getErrorString(int i) throws IBScanException {
        NativeError nativeError = new NativeError();
        String errorStringNative = getErrorStringNative(i, nativeError);
        handleError(nativeError);
        return errorStringNative;
    }
    public int getInitProgress(int i) throws IBScanException {
        NativeError nativeError = new NativeError();
        int initProgressNative = getInitProgressNative(i, nativeError);
        handleError(nativeError);
        return initProgressNative;
    }
    public String getRequiredSDKVersion(int i) throws IBScanException {
        NativeError nativeError = new NativeError();
        String requiredSDKVersionNative = getRequiredSDKVersionNative(i, nativeError);
        handleError(nativeError);
        return requiredSDKVersionNative;
    }
    public SdkVersion getSdkVersion() throws IBScanException {
        NativeError nativeError = new NativeError();
        SdkVersion sdkVersionNative = getSdkVersionNative(nativeError);
        handleError(nativeError);
        return sdkVersionNative;
    }
    public boolean hasPermission(int i) {
        UsbDevice findDevice = findDevice(i);
        if (findDevice != null) {
            return ((UsbManager) this.m_context.getSystemService("usb")).hasPermission(findDevice);
        }
        return false;
    }
    public IBScanDevice openDevice(int i) throws IBScanException {
        NativeError nativeError = new NativeError();
        IBScanDevice openDeviceNative = openDeviceNative(i, nativeError);
        handleError(nativeError);
        return openDeviceNative;
    }
    public void openDeviceAsync(int i) throws IBScanException {
        NativeError nativeError = new NativeError();
        openDeviceAsyncNative(i, nativeError);
        handleError(nativeError);
    }
    public void requestPermission(int i) {
        UsbDevice findDevice = findDevice(i);
        if (findDevice != null) {
            ((UsbManager) this.m_context.getSystemService("usb")).requestPermission(findDevice, PendingIntent.getBroadcast(this.m_context, 0, new Intent(ACTION_USB_PERMISSION), 0));
        }
    }
    public void setContext(Context context) {
        Context context2 = this.m_context;
        if (context2 != null) {
            context2.unregisterReceiver(this.m_usbReceiver);
            this.m_context = null;
            LibUsbManager.m_context = null;
        }
        if (context != null) {
            this.m_context = context;
            LibUsbManager.m_context = this.m_context;
            IntentFilter intentFilter = new IntentFilter();
            intentFilter.addAction("android.hardware.usb.action.USB_DEVICE_ATTACHED");
            intentFilter.addAction("android.hardware.usb.action.USB_DEVICE_DETACHED");
            intentFilter.addAction(ACTION_USB_PERMISSION);
            this.m_context.registerReceiver(this.m_usbReceiver, intentFilter);
        }
    }
    public void setCustomerKey(int i, HashType hashType, String str) throws IBScanException {
        NativeError nativeError = new NativeError();
        setCustomerKeyNative(i, hashType.toCode(), str, nativeError);
        handleError(nativeError);
    }
    public void setScanListener(IBScanListener iBScanListener) {
        this.m_listener = iBScanListener;
    }
    public void unloadLibrary() throws IBScanException {
        NativeError nativeError = new NativeError();
        unloadLibraryNative(nativeError);
        handleError(nativeError);
    }
    public void updateUsbPermission() {
        updateUsbPermissionNative();
    }
    public IBScanDevice openDevice(int i, String str) throws IBScanException {
        if (str != null) {
            NativeError nativeError = new NativeError();
            IBScanDevice openDeviceExNative = openDeviceExNative(i, str, nativeError);
            handleError(nativeError);
            return openDeviceExNative;
        }
        String str2 = getMethodName() + ": receive null uniformityMaskPath";
        throw new IllegalArgumentException();
    }
    public void openDeviceAsync(int i, String str) throws IBScanException {
        if (str != null) {
            NativeError nativeError = new NativeError();
            openDeviceAsyncExNative(i, str, nativeError);
            handleError(nativeError);
        } else {
            String str2 = getMethodName() + ": receive null uniformityMaskPath";
            throw new IllegalArgumentException();
        }
    }
}
