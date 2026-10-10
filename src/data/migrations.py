from pymongo.database import Database
import datetime

class MigrationManager:
    def __init__(self, db: Database):
        self.db = db
        self.collection = db['schema_migrations']
    
    def initialize(self):
        
        if 'schema_migrations' not in self.db.list_collection_names():
            self.db.create_collection('schema_migrations')
            self.collection.create_index('version', unique=True)
    
    def apply_migration(self, version: str, description: str, up_func):
        """Applies a single migration if it hasn't been applied yet."""
        migration = self.collection.find_one({"version": version})
        if migration:
            print(f"Migration {version} already applied.")
            return

        print(f"Applying migration {version}: {description}")
        try:
            up_func(self.db)
            self.collection.insert_one({
                "version": version,
                "description": description,
                "applied_at": datetime.datetime.utcnow(),
                "checksum": "TODO" 
            })
            print(f"Migration {version} applied successfully.")
        except Exception as e:
            print(f"Error applying migration {version}: {e}")
            raise
