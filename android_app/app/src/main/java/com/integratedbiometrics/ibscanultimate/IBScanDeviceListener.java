package com.integratedbiometrics.ibscanultimate;
import com.integratedbiometrics.ibscanultimate.IBScanDevice;
public interface IBScanDeviceListener {
    void deviceAcquisitionBegun(IBScanDevice iBScanDevice, IBScanDevice.ImageType imageType);
    void deviceAcquisitionCompleted(IBScanDevice iBScanDevice, IBScanDevice.ImageType imageType);
    void deviceCommunicationBroken(IBScanDevice iBScanDevice);
    void deviceFingerCountChanged(IBScanDevice iBScanDevice, IBScanDevice.FingerCountState fingerCountState);
    void deviceFingerQualityChanged(IBScanDevice iBScanDevice, IBScanDevice.FingerQualityState[] fingerQualityStateArr);
    void deviceImagePreviewAvailable(IBScanDevice iBScanDevice, IBScanDevice.ImageData imageData);
    void deviceImageResultAvailable(IBScanDevice iBScanDevice, IBScanDevice.ImageData imageData, IBScanDevice.ImageType imageType, IBScanDevice.ImageData[] imageDataArr);
    void deviceImageResultExtendedAvailable(IBScanDevice iBScanDevice, IBScanException iBScanException, IBScanDevice.ImageData imageData, IBScanDevice.ImageType imageType, int i, IBScanDevice.ImageData[] imageDataArr, IBScanDevice.SegmentPosition[] segmentPositionArr);
    void devicePlatenStateChanged(IBScanDevice iBScanDevice, IBScanDevice.PlatenState platenState);
    void devicePressedKeyButtons(IBScanDevice iBScanDevice, int i);
    void deviceWarningReceived(IBScanDevice iBScanDevice, IBScanException iBScanException);
}
