package com.integratedbiometrics.ibscancommon;
public class IBCommon {
    public enum CaptureDeviceTechId {
        UNKNOWN_OR_UNSPECIFIED(0),
        WHITE_LIGHT_OPTICAL_TIR(1),
        WHITE_LIGHT_OPTICAL_DIRECT_VIEW_ON_PLATEN(2),
        WHITE_LIGHT_OPTICAL_TOUCHLESS(3),
        MONOCHROMATIC_VISIBLE_OPTICAL_TIR(4),
        MONOCHROMATIC_VISIBLE_OPTICAL_DIRECT_VIEW_ON_PLATEN(5),
        MONOCHROMATIC_VISIBLE_OPTICAL_TOUCHLESS(6),
        MONOCHROMATIC_IR_OPTICAL_TIR(7),
        MONOCHROMATIC_IR_OPTICAL_DIRECT_VIEW_ON_PLATEN(8),
        MONOCHROMATIC_IR_OPTICAL_TOUCHLESS(9),
        MULTISPECTRAL_OPTICAL_TIR(10),
        MULTISPECTRAL_OPTICAL_DIRECT_VIEW_ON_PLATEN(11),
        MULTISPECTRAL_OPTICAL_TOUCHLESS(12),
        ELECTRO_LUMINESCENT(13),
        SEMICONDUCTOR_CAPACITIVE(14),
        SEMICONDUCTOR_RF(15),
        SEMICONDUCTOR_THEMAL(16),
        PRESSURE_SENSITIVE(17),
        ULTRASOUND(18),
        MECHANICAL(19),
        GLASS_FIBER(20);
        public final int code;
        CaptureDeviceTechId(int i) {
            this.code = i;
        }
        public static CaptureDeviceTechId fromCode(int i) {
            for (CaptureDeviceTechId captureDeviceTechId : values()) {
                if (captureDeviceTechId.code == i) {
                    return captureDeviceTechId;
                }
            }
            return null;
        }
        public final int toCode() {
            return this.code;
        }
    }
    public enum FingerPosition {
        UNKNOWN(0),
        RIGHT_THUMB(1),
        RIGHT_INDEX_FINGER(2),
        RIGHT_MIDDLE_FINGER(3),
        RIGHT_RING_FINGER(4),
        RIGHT_LITTLE_FINGER(5),
        LEFT_THUMB(6),
        LEFT_INDEX_FINGER(7),
        LEFT_MIDDLE_FINGER(8),
        LEFT_RING_FINGER(9),
        LEFT_LITTLE_FINGER(10),
        PLAIN_RIGHT_FOUR_FINGERS(13),
        PLAIN_LEFT_FOUR_FINGERS(14),
        PLAIN_THUMBS(15),
        UNKNOWN_PALM(20),
        RIGHT_FULL_PALM(21),
        RIGHT_WRITERS_PALM(22),
        LEFT_FULL_PALM(23),
        LEFT_WRITERS_PALM(24),
        RIGHT_LOWER_PALM(25),
        RIGHT_UPPER_PALM(26),
        LEFT_LOWER_PALM(27),
        LEFT_UPPER_PALM(28),
        RIGHT_OTHER(29),
        LEFT_OTHER(30),
        RIGHT_INTERDIGITAL(31),
        RIGHT_THENAR(32),
        RIGHT_HYPOTHENAR(33),
        LEFT_INTERDIGITAL(34),
        LEFT_THENAR(35),
        LEFT_HYPOTHENAR(36),
        RIGHT_INDEX_AND_MIDDLE(40),
        RIGHT_MIDDLE_AND_RING(41),
        RIGHT_RING_AND_LITTLE(42),
        LEFT_INDEX_AND_MIDDLE(43),
        LEFT_MIDDLE_AND_RING(44),
        LEFT_RING_AND_LITTLE(45),
        RIGHT_INDEX_AND_LEFT_INDEX(46),
        RIGHT_INDEX_AND_MIDDLE_AND_RING(47),
        RIGHT_MIDDLE_AND_RING_AND_LITTLE(48),
        LEFT_INDEX_AND_MIDDLE_AND_RING(49),
        LEFT_MIDDLE_AND_RING_AND_LITTLE(50);
        public final int code;
        FingerPosition(int i) {
            this.code = i;
        }
        public static FingerPosition fromCode(int i) {
            for (FingerPosition fingerPosition : values()) {
                if (fingerPosition.code == i) {
                    return fingerPosition;
                }
            }
            return null;
        }
        public final int toCode() {
            return this.code;
        }
    }
    public static class ImageDataExt {
        public final byte bitDepth;
        public final CaptureDeviceTechId captureDeviceTechId;
        public final short captureDeviceTypeId;
        public final short captureDeviceVendorId;
        public final FingerPosition fingerPosition;
        public final byte[] imageData;
        public final ImageFormat imageFormat;
        public final short imageSamplingX;
        public final short imageSamplingY;
        public final short imageSizeX;
        public final short imageSizeY;
        public final ImpressionType impressionType;
        public final byte scaleUnit;
        public final short scanSamplingX;
        public final short scanSamplingY;
        public ImageDataExt(int i, int i2, int i3, int i4, short s, short s2, short s3, short s4, short s5, short s6, short s7, short s8, byte b, byte b2, byte[] bArr) {
            this.imageFormat = ImageFormat.fromCode(i);
            this.impressionType = ImpressionType.fromCode(i2);
            this.fingerPosition = FingerPosition.fromCode(i3);
            this.captureDeviceTechId = CaptureDeviceTechId.fromCode(i4);
            this.captureDeviceVendorId = s;
            this.captureDeviceTypeId = s2;
            this.scanSamplingX = s3;
            this.scanSamplingY = s4;
            this.imageSamplingX = s5;
            this.imageSamplingY = s6;
            this.imageSizeX = s7;
            this.imageSizeY = s8;
            this.scaleUnit = b;
            this.bitDepth = b2;
            this.imageData = bArr;
        }
        public String toString() {
            StringBuilder sb = new StringBuilder("Image format = ");
            sb.append(this.imageFormat.toString());
            sb.append("\nImpression type = ");
            sb.append(this.impressionType.toString());
            sb.append("\nFinger position = ");
            sb.append(this.fingerPosition.toString());
            sb.append("\nCapture device tech ID = ");
            sb.append(this.captureDeviceTechId.toString());
            sb.append("\nCapture device vendor ID = ");
            sb.append((int) this.captureDeviceVendorId);
            sb.append("\nCapture device type ID = ");
            sb.append((int) this.captureDeviceTypeId);
            sb.append("\nScan sampling = ");
            sb.append((int) this.scanSamplingX);
            sb.append(" x ");
            sb.append((int) this.scanSamplingY);
            sb.append("\nImage sampling = ");
            sb.append((int) this.imageSamplingX);
            sb.append(" x ");
            sb.append((int) this.imageSamplingY);
            sb.append("\nImage size = ");
            sb.append((int) this.imageSizeX);
            sb.append(" x ");
            sb.append((int) this.imageSizeY);
            sb.append("\nScale unit = ");
            return sb.append(this.scaleUnit).append("\n").toString();
        }
    }
    public enum ImageFormat {
        NO_BIT_PACKING(0),
        BIT_PACKED(1),
        WSQ(2),
        JPEG_LOSSY(3),
        JPEG2000_LOSSY(4),
        JPEG2000_LOSSLESS(5),
        PNG(6);
        public final int code;
        ImageFormat(int i) {
            this.code = i;
        }
        public static ImageFormat fromCode(int i) {
            for (ImageFormat imageFormat : values()) {
                if (imageFormat.code == i) {
                    return imageFormat;
                }
            }
            return null;
        }
        public final int toCode() {
            return this.code;
        }
    }
    public enum ImpressionType {
        LIVE_SCAN_PLAIN(0),
        LIVE_SCAN_ROLLED(1),
        NONLIVE_SCAN_PLAIN(2),
        NONLIVE_SCAN_ROLLED(3),
        LATENT_IMPRESSION(4),
        LATENT_TRACING(5),
        LATENT_PHOTO(6),
        LATENT_LIFT(7),
        LIVE_SCAN_SWIPE(8),
        LIVE_SCAN_VERTICAL_ROLL(9),
        LIVE_SCAN_PALM(10),
        NONLIVE_SCAN_PALM(11),
        LATENT_PALM_IMPRESSION(12),
        LATENT_PALM_TRACING(13),
        LATENT_PALM_PHOTO(14),
        LATENT_PALM_LIFT(15),
        LIVE_SCAN_OPTICAL_CONTRCTLESS_PLAIN(24),
        OTHER(28),
        UNKNOWN(29);
        public final int code;
        ImpressionType(int i) {
            this.code = i;
        }
        public static ImpressionType fromCode(int i) {
            for (ImpressionType impressionType : values()) {
                if (impressionType.code == i) {
                    return impressionType;
                }
            }
            return null;
        }
        public final int toCode() {
            return this.code;
        }
    }
}
