"""Restricted, one-time conversion of old NumPy templates; never used by the API."""
import io
import pickle
import zlib
import numpy as np


class TemplateReader(pickle.Unpickler):
    def find_class(self, module, name):
        allowed = {
            ('numpy', 'ndarray'): np.ndarray,
            ('numpy', 'dtype'): np.dtype,
            ('numpy.core.multiarray', '_reconstruct'): np._core.multiarray._reconstruct,
            ('numpy._core.multiarray', '_reconstruct'): np._core.multiarray._reconstruct,
            ('numpy.core.numeric', '_frombuffer'): np._core.numeric._frombuffer,
            ('numpy._core.numeric', '_frombuffer'): np._core.numeric._frombuffer,
        }
        if (module, name) not in allowed:
            raise ValueError('Unsupported legacy template type; re-enrollment required.')
        return allowed[(module, name)]


def convert_templates(db):
    converted = failed = 0
    for employee in db.employees.find({'fingerprint_descriptors': {'$exists': True},
                                     'fingerprint_samples': {'$exists': False}}):
        try:
            raw = employee['fingerprint_descriptors']
            if len(raw) > 1_000_000:
                raise ValueError('Template too large')
            if raw[:1] != b'\x80':
                raw = zlib.decompressobj().decompress(raw, 1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError('Template too large')
            arrays = TemplateReader(io.BytesIO(raw)).load()
            if isinstance(arrays, np.ndarray):
                arrays = [arrays]
            if not isinstance(arrays, list) or not 1 <= len(arrays) <= 3:
                raise ValueError('Invalid template list')
            for array in arrays:
                if not isinstance(array, np.ndarray) or array.dtype != np.uint8 or array.ndim != 2 or not (
                        20 <= array.shape[0] <= 2000 and array.shape[1] == 32):
                    raise ValueError('Invalid template shape')
            db.employees.update_one({'_id': employee['_id']}, {'$set': {
                'fingerprint_samples': [array.tolist() for array in arrays], 'has_fingerprint': True}})
            converted += 1
        except Exception:
            db.employees.update_one({'_id': employee['_id']}, {'$set': {'has_fingerprint': False}})
            failed += 1
    return converted, failed
