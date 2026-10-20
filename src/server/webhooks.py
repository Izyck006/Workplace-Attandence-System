"""Payment webhook signature verifiers for Paystack and Stripe."""
import hashlib
import hmac
import time
from typing import Optional


def verify_paystack_signature(payload: bytes, signature_header: Optional[str], secret_key: str) -> bool:
    """
    Verify Paystack webhook signature using HMAC-SHA512.
    Header: 'x-paystack-signature'
    """
    if not signature_header or not secret_key:
        return False
    computed = hmac.new(
        secret_key.encode("utf-8"),
        payload,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed.lower(), signature_header.strip().lower())


def verify_stripe_signature(payload: bytes, signature_header: Optional[str], secret_key: str, tolerance: int = 300) -> bool:
    """
    Verify Stripe webhook signature using HMAC-SHA256 with timestamp tolerance check.
    Header: 'stripe-signature' format: 't=timestamp,v1=signature'
    """
    if not signature_header or not secret_key:
        return False

    elements = signature_header.split(",")
    timestamp = None
    signatures = []
    for item in elements:
        parts = item.strip().split("=", 1)
        if len(parts) == 2:
            key, val = parts[0].strip(), parts[1].strip()
            if key == "t":
                try:
                    timestamp = int(val)
                except ValueError:
                    return False
            elif key == "v1":
                signatures.append(val)

    if timestamp is None or not signatures:
        return False

    # Prevent replay attacks: check timestamp tolerance
    if abs(time.time() - timestamp) > tolerance:
        return False

    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    computed = hmac.new(
        secret_key.encode("utf-8"),
        signed_payload,
        hashlib.sha256
    ).hexdigest()

    return any(hmac.compare_digest(computed.lower(), sig.lower()) for sig in signatures)
