import cv2
import numpy as np

class FingerprintMatcher:
    def __init__(self):
        self.detector = cv2.ORB_create(nfeatures=2000)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def extract_descriptors(self, image_bytes, width, height):
        if not image_bytes or width == 0 or height == 0:
            return None
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = img_array.reshape((height, width))
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
        keypoints, descriptors = self.detector.detectAndCompute(img, None)
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
                if d < 25:
                    score += 20
                elif d < 30:
                    score += 10
                elif d < 35:
                    score += 4
                elif d < 40:
                    score += 1
            return score
        except Exception:
            return 0
