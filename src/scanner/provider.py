from typing import Optional, Protocol, Tuple

class ScannerProvider(Protocol):
    def initialize(self) -> bool:
        """Initialize the scanner hardware/SDK."""
        ...
        
    def capture_template(self) -> Tuple[bool, Optional[bytes], int]:
        """
        Captures a fingerprint and returns a template.
        Returns (success, template_bytes, quality_score)
        """
        ...
        
    def identify(self, template: bytes, stored_templates: dict) -> Optional[str]:
        """
        Matches a scanned template against enrolled templates.
        stored_templates is a mapping of employee_id -> template_bytes
        Returns the matching employee_id or None
        """
        ...
        
    def close(self):
        """Release scanner resources."""
        ...

class KojackVendorProvider:
    def __init__(self):
        self._is_initialized = False
        self.scanner = None
        
    def initialize(self) -> bool:
        from src.scanner.kojack import KojackScanner
        if self.scanner:
            self.scanner.close_device()
        self._is_initialized = False
        self.scanner = KojackScanner()
        
        
        count = self.scanner.get_device_count()
        if count == 0:
            print("KojackVendorProvider: No Kojack devices found.")
            return False
            
        
        if self.scanner.open_device(0):
            print("KojackVendorProvider: Initialized and opened Kojack device.")
            self._is_initialized = True
            return True
            
        print("KojackVendorProvider: Failed to open Kojack device.")
        return False
        
    def capture_template(self) -> Tuple[bool, Optional[bytes], int]:
        if not self._is_initialized:
            return False, None, 0
            
        
        
        
        print("KojackVendorProvider: capture_template is stubbed.")
        return False, None, 0

    def identify(self, template: bytes, stored_templates: dict) -> Optional[str]:
        
        print("KojackVendorProvider: identify is stubbed.")
        return None
        
    def close(self):
        if self.scanner:
            self.scanner.close_device()
        self._is_initialized = False

class MockProvider(ScannerProvider):
    """
    A simulated scanner provider that doesn't require physical hardware.
    Useful for testing the UI and database logic before the SDK is available.
    """
    def __init__(self):
        self._is_initialized = False
        import uuid
        self.mock_template = uuid.uuid4().bytes
        
    def initialize(self) -> bool:
        print("MockProvider: Initialized virtual scanner")
        self._is_initialized = True
        return True
        
    def capture_template(self) -> Tuple[bool, Optional[bytes], int]:
        if not self._is_initialized:
            return False, None, 0
            
        print("MockProvider: Captured mock fingerprint")
        
        return True, self.mock_template, 100

    def identify(self, template: bytes, stored_templates: dict) -> Optional[str]:
        
        for emp_id, emp_template in stored_templates.items():
            if template == emp_template:
                return emp_id
        return None
        
    def close(self):
        print("MockProvider: Closed virtual scanner")
        self._is_initialized = False
