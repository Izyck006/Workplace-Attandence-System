import os
import sys
import pickle
import zlib
import cv2
from bson import ObjectId


sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database import DatabaseManager
from src.services.fingerprint import FingerprintMatcher

def test_matching():
    db = DatabaseManager.get_db()
    
    
    emp = db.employees.find_one({"has_fingerprint": True})
    if not emp:
        print("No employee found with fingerprints enrolled.")
        return
        
    print(f"Testing with Employee ID: {emp['_id']}, Name: {emp.get('first_name', 'Unknown')}")
    
    raw_bytes = None
    if "fingerprint_descriptors" in emp:
        try:
            raw_bytes = zlib.decompress(emp["fingerprint_descriptors"])
            print("Successfully decompressed zlib payload.")
        except Exception as e:
            raw_bytes = emp["fingerprint_descriptors"]
            print("Payload was not compressed or decompression failed:", str(e))
            
    if not raw_bytes:
        print("No descriptor bytes found.")
        return
        
    try:
        db_desc_data = pickle.loads(raw_bytes)
        print(f"Successfully unpickled descriptors. Found {len(db_desc_data)} templates.")
    except Exception as e:
        print("Failed to unpickle:", str(e))
        return
        
    if len(db_desc_data) < 2:
        print("Need at least 2 templates to test matching against each other.")
        return
        
    template1 = db_desc_data[0]
    template2 = db_desc_data[1]
    
    print(f"Template 1 shape: {template1.shape if template1 is not None else 'None'}")
    print(f"Template 2 shape: {template2.shape if template2 is not None else 'None'}")
    
    matcher = FingerprintMatcher()
    
    if template1 is not None and template2 is not None:
        try:
            matches = matcher.bf.match(template1, template2)
            print(f"Total raw matches found: {len(matches)}")
            
            
            matches = sorted(matches, key=lambda x: x.distance)
            print("Top 10 match distances:")
            for m in matches[:10]:
                print(f"  Distance: {m.distance}")
                
            score = matcher.get_match_score(template1, template2, threshold=50)
            print(f"Good matches (threshold < 50): {score}")
            
            score_70 = matcher.get_match_score(template1, template2, threshold=70)
            print(f"Good matches (threshold < 70): {score_70}")
            
        except Exception as e:
            print(f"Error during matching: {e}")

if __name__ == "__main__":
    test_matching()
