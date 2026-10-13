package com.integratedbiometrics.ibscanultimate;
public class IBScanException extends Exception {
    public final Type type;
    public enum Type {
        INVALID_PARAM_VALUE(-1),
        MEM_ALLOC(-2),
        NOT_SUPPORTED(-3),
        FILE_OPEN(-4),
        FILE_READ(-5),
        RESOURCE_LOCKED(-6),
        MISSING_RESOURCE(-7),
        INVALID_ACCESS_POINTER(-8),
        THREAD_CREATE(-9),
        COMMAND_FAILED(-10),
        LIBRARY_UNLOAD_FAILED(-11),
        CHANNEL_IO_COMMAND_FAILED(-100),
        CHANNEL_IO_READ_FAILED(-101),
        CHANNEL_IO_WRITE_FAILED(-102),
        CHANNEL_IO_READ_TIMEOUT(-103),
        CHANNEL_IO_WRITE_TIMEOUT(-104),
        CHANNEL_IO_UNEXPECTED_FAILED(-105),
        CHANNEL_IO_INVALID_HANDLE(-106),
        CHANNEL_IO_WRONG_PIPE_INDEX(-107),
        DEVICE_IO(-200),
        DEVICE_NOT_FOUND(-201),
        DEVICE_NOT_MATCHED(-202),
        DEVICE_ACTIVE(-203),
        DEVICE_NOT_INITIALIZED(-204),
        DEVICE_INVALID_STATE(-205),
        DEVICE_BUSY(-206),
        DEVICE_NOT_SUPPORTED_FEATURE(-207),
        INVALID_LICENSE(-208),
        USB20_REQUIRED(-209),
        DEVICE_ENABLED_POWER_SAVE_MODE(-210),
        DEVICE_NEED_UPDATE_FIRMWARE(-211),
        DEVICE_NEED_CALIBRATE_TOF(-212),
        DEVICE_INVALID_CALIBRATION_DATA(-213),
        DEVICE_HIGHER_SDK_REQUIRED(-214),
        DEVICE_LOCK_INVALID_BUFF(-215),
        DEVICE_LOCK_INFO_EMPTY(-216),
        DEVICE_LOCK_INFO_NOT_MATCHED(-217),
        DEVICE_LOCK_INVALID_CHECKSUM(-218),
        DEVICE_LOCK_INVALID_KEY(-219),
        DEVICE_LOCK_LOCKED(-220),
        DEVICE_LOCK_ILLEGAL_DEVICE(-221),
        DEVICE_NOT_ACCESSIBLE(-299),
        CAPTURE_COMMAND_FAILED(-300),
        CAPTURE_STOP(-301),
        CAPTURE_TIMEOUT(-302),
        CAPTURE_STILL_RUNNING(-303),
        CAPTURE_NOT_RUNNING(-304),
        CAPTURE_INVALID_MODE(-305),
        CAPTURE_ALGORITHM(-306),
        CAPTURE_ROLLING(-307),
        CAPTURE_ROLLING_TIMEOUT(-308),
        NBIS_NFIQ_FAILED(-500),
        NBIS_WSQ_ENCODE_FAILED(-501),
        NBIS_WSQ_DECODE_FAILED(-502),
        DUPLICATE_EXTRACTION_FAILED(-600),
        DUPLICATE_ALREADY_USED(-601),
        DUPLICATE_SEGMENTATION_FAILED(-602),
        DUPLICATE_MATCHING_FAILED(-603),
        CHANNEL_IO_FRAME_MISSING(100),
        CHANNEL_IO_CAMERA_WRONG(101),
        CHANNEL_IO_SLEEP_STATUS(102),
        OUTDATED_FIRMWARE(200),
        ALREADY_INITIALIZED(201),
        API_DEPRECATED(202),
        ALREADY_ENHANCED_IMAGE(203),
        BGET_IMAGE(300),
        ROLLING_NOT_RUNNING(301),
        NO_FINGER(302),
        INCORRECT_FINGERS(303),
        ROLLING_SMEAR(304),
        ROLLING_SHIFTED_HORIZONTALLY(305),
        ROLLING_SHIFTED_VERTICALLY(306),
        ROLLING_SHIFTED_HORIZONTALLY_VERTICALLY(307),
        EMPTY_IBSM_RESULT_IMAGE(400),
        QUALITY_INVALID_AREA(512),
        QUALITY_INVALID_AREA_HORIZONTALLY(513),
        QUALITY_INVALID_AREA_VERTICALLY(514),
        QUALITY_INVALID_AREA_HORIZONTALLY_VERTICALLY(515),
        INVALID_BRIGHTNESS_FINGERS(600),
        WET_FINGERS(601),
        MULTIPLE_FINGERS_DURING_ROLL(602),
        SPOOF_DETECTED(603),
        SLIP_DETECTED(604),
        SPOOF_INIT_FAILED(605);
        public final int code;
        Type(int i) {
            this.code = i;
        }
        public static Type fromCode(int i) {
            for (Type type : values()) {
                if (type.code == i) {
                    return type;
                }
            }
            return null;
        }
        public final int toCode() {
            return this.code;
        }
    }
    public IBScanException(Type type) {
        this.type = type;
    }
    public Type getType() {
        return this.type;
    }
}
