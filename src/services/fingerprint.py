import cv2
import numpy as np

class FingerprintMatcher:
    def __init__(self):
        self.detector = cv2.ORB_create(nfeatures=2000)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)

    def extract_descriptors(self, image_bytes, width, height):
        if not image_bytes or width == 0 or height == 0:
            return None
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = img_array.reshape((height, width))
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
        keypoints, descriptors = self.detector.detectAndCompute(img, None)
        return descriptors

    def get_match_score(self, descriptors_probe, descriptors_db, threshold=45, ratio=0.75):
        if descriptors_probe is None or descriptors_db is None:
            return 0
        if len(descriptors_probe) < 2 or len(descriptors_db) < 2:
            return 0
        try:
            matches_fwd = self.bf.knnMatch(descriptors_probe, descriptors_db, k=2)
            fwd_good = {}
            for pair in matches_fwd:
                if len(pair) == 2:
                    m, n = pair
                    if m.distance <= threshold and m.distance < ratio * n.distance:
                        fwd_good[m.queryIdx] = m.trainIdx
            matches_bwd = self.bf.knnMatch(descriptors_db, descriptors_probe, k=2)
            mutual_count = 0
            for pair in matches_bwd:
                if len(pair) == 2:
                    m, n = pair
                    if m.distance <= threshold and m.distance < ratio * n.distance:
                        if fwd_good.get(m.trainIdx) == m.queryIdx:
                            mutual_count += 1
            return mutual_count
        except Exception:
            return 0
