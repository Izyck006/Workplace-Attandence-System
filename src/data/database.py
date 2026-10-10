import os
from pymongo import MongoClient
from pymongo.database import Database

class DatabaseManager:
    _client: MongoClient = None
    _db: Database = None

    @classmethod
    def get_client(cls) -> MongoClient:
        if cls._client is None:
            import certifi
            from dotenv import load_dotenv
            load_dotenv()
            uri = os.getenv("MONGODB_URI")
            if not uri:
                raise ValueError("MONGODB_URI not found in .env file")
            
            cls._client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        return cls._client

    @classmethod
    def get_db(cls, db_name: str = "attendance_db") -> Database:
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[db_name]
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
