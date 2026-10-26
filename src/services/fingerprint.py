import cv2
import numpy as np


class FingerprintMatcher:
    def __init__(self, nfeatures=500):
        self.detector = cv2.ORB_create(
            nfeatures=nfeatures,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=15,
            patchSize=31
        )
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def extract_descriptors(self, image_bytes, width, height):
        if not image_bytes or width == 0 or height == 0:
            return None
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = img_array.reshape((height, width))

        filtered = cv2.bilateralFilter(img, d=5, sigmaColor=50, sigmaSpace=50)

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(filtered)

        keypoints, descriptors = self.detector.detectAndCompute(enhanced, None)
        return descriptors

    def get_match_score(self, descriptors_probe, descriptors_db):
        if descriptors_probe is None or descriptors_db is None:
            return 0
        if len(descriptors_probe) < 2 or len(descriptors_db) < 2:
            return 0
        try:
            matches = self.bf.match(descriptors_probe, descriptors_db)
            score = 0
            for m in matches:
                d = m.distance
                if d < 28:
                    score += 25
                elif d < 38:
                    score += 15
                elif d < 48:
                    score += 8
                elif d < 58:
                    score += 3
            return score
        except Exception:
            return 0

