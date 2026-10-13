package com.integratedbiometrics.ibscanultimate;
public interface IBScanListener {
    void scanDeviceAttached(int i);
    void scanDeviceCountChanged(int i);
    void scanDeviceDetached(int i);
    void scanDeviceInitProgress(int i, int i2);
    void scanDeviceOpenComplete(int i, IBScanDevice iBScanDevice, IBScanException iBScanException);
    void scanDevicePermissionGranted(int i, boolean z);
}
