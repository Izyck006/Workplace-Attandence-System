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
            from pathlib import Path
            load_dotenv(Path(__file__).resolve().parents[2] / '.env')
            uri = os.getenv("MONGODB_URI")
            if not uri:
                raise ValueError("MONGODB_URI not found in .env file")
            
            options = {"serverSelectionTimeoutMS": 5000, "connectTimeoutMS": 5000, "socketTimeoutMS": 15000}
            if uri.startswith('mongodb+srv:'):
                try:
                    import dns.resolver
                    res = dns.resolver.get_default_resolver()
                    fallback = ['8.8.8.8', '1.1.1.1']
                    res.nameservers = [ns for ns in fallback if ns not in res.nameservers] + res.nameservers
                except Exception:
                    pass
            if uri.startswith('mongodb+srv:') or 'tls=true' in uri.lower():
                options['tlsCAFile'] = certifi.where()
            cls._client = MongoClient(uri, **options)
        return cls._client

    @classmethod
    def get_db(cls, db_name: str = "attendance_db") -> Database:
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[os.getenv('MONGODB_DATABASE', db_name)]
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
