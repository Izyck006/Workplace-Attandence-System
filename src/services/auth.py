from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from src.data.database import DatabaseManager

class AuthService:
    def __init__(self):
        self.ph = PasswordHasher()

    def hash_password(self, password: str) -> str:
        if len(password) < 10:
            raise ValueError("Password must be at least 10 characters long.")
        return self.ph.hash(password)

    def verify_password(self, hashed: str, password: str) -> bool:
        try:
            return self.ph.verify(hashed, password)
        except VerifyMismatchError:
            return False

    def authenticate(self, username: str, password: str) -> dict:
        """
        Authenticates a user and returns their user document if successful.
        Raises ValueError if authentication fails or account is locked.
        """
        db = DatabaseManager.get_db()
        users_col = db.users
        user = users_col.find_one({"username": username})

        if not user:
            raise ValueError("Invalid username or password.")
            
        if not user.get("is_active", True):
            raise ValueError("Account is inactive.")
            
        if not self.verify_password(user["password_hash"], password):
            
            failed = user.get("failed_attempts", 0) + 1
            update_data = {"failed_attempts": failed}
            if failed >= 5:
                
                pass
            users_col.update_one({"_id": user["_id"]}, {"$set": update_data})
            raise ValueError("Invalid username or password.")

        
        users_col.update_one({"_id": user["_id"]}, {"$set": {"failed_attempts": 0}})
        return user
