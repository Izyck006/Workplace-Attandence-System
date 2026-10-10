import cv2
import numpy as np

class FingerprintMatcher:
    def __init__(self):
        
        self.detector = cv2.ORB_create(nfeatures=2000)
        
        
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def extract_descriptors(self, image_bytes, width, height):
        """Extracts SIFT descriptors from raw 8-bit grayscale image bytes."""
        if not image_bytes or width == 0 or height == 0:
            return None
            
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = img_array.reshape((height, width))
        
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img = clahe.apply(img)
        
        keypoints, descriptors = self.detector.detectAndCompute(img, None)
        return descriptors

    def get_match_score(self, descriptors_probe, descriptors_db, threshold=50):
        """Returns the number of good minutiae matches between two fingerprints."""
        if descriptors_probe is None or descriptors_db is None:
            return 0
        if len(descriptors_probe) < 2 or len(descriptors_db) < 2:
            return 0
            
        try:
            matches = self.bf.match(descriptors_probe, descriptors_db)
        except Exception:
            return 0
        
        
        good_matches = 0
        for m in matches:
            if m.distance < threshold:
                good_matches += 1
                    
        return good_matches
