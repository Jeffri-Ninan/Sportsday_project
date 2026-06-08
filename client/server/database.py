import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

MONGO_URI = os.getenv("MONGO_URI")
db_instance = None

class MockCollection:
    def __init__(self, name, db_parent=None, default_data=None):
        self.name = name
        self.db_parent = db_parent
        self.docs = default_data or []
        
    def _match_doc(self, doc, query):
        if not query:
            return True
        import re
        for k, v in query.items():
            val = doc.get(k)
            if isinstance(v, dict) and "$regex" in v:
                pattern = v["$regex"]
                options = v.get("$options", "")
                flags = 0
                if "i" in options:
                    flags |= re.IGNORECASE
                if not re.search(pattern, str(val or ""), flags):
                    return False
            elif k == "_id":
                if str(val) != str(v):
                    return False
            elif val != v:
                return False
        return True

    def find_one(self, query):
        for doc in self.docs:
            if self._match_doc(doc, query):
                return doc
        return None
        
    def find(self, query=None):
        results = []
        for doc in self.docs:
            if self._match_doc(doc, query):
                results.append(doc)
        return results
        
    def insert_one(self, doc):
        if "_id" not in doc:
            from bson import ObjectId
            doc["_id"] = ObjectId()
        self.docs.append(doc)
        if self.db_parent:
            self.db_parent.save_to_file()
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertOneResult(doc["_id"])
        
    def insert_many(self, docs):
        for doc in docs:
            self.insert_one(doc)
        if self.db_parent:
            self.db_parent.save_to_file()
        return docs
        
    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc and "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
            if self.db_parent:
                self.db_parent.save_to_file()
            class UpdateResult:
                def __init__(self, matched_count, modified_count):
                    self.matched_count = matched_count
                    self.modified_count = modified_count
            return UpdateResult(1, 1)
        class UpdateResult:
            def __init__(self, matched_count, modified_count):
                self.matched_count = matched_count
                self.modified_count = modified_count
        return UpdateResult(0, 0)
        
    def delete_one(self, query):
        doc = self.find_one(query)
        if doc:
            self.docs.remove(doc)
            if self.db_parent:
                self.db_parent.save_to_file()
            class DeleteResult:
                def __init__(self, deleted_count):
                    self.deleted_count = deleted_count
            return DeleteResult(1)
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        return DeleteResult(0)
        
    def delete_many(self, query):
        to_delete = [doc for doc in self.docs if self._match_doc(doc, query)]
        for doc in to_delete:
            self.docs.remove(doc)
        if self.db_parent and to_delete:
            self.db_parent.save_to_file()
        
    def count_documents(self, query):
        return len(self.find(query))

class MockDatabase:
    def __init__(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_db.json")
        self.file_path = file_path
        self.collections = {}
        self.load_from_file()
        
    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name, self)
        return self.collections[name]

    def load_from_file(self):
        import json
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for col_name, docs in data.items():
                        self.collections[col_name] = MockCollection(col_name, self, docs)
                print(f"Loaded MockDatabase state from {self.file_path}")
            except Exception as e:
                print(f"Error loading mock database file: {e}")
                
    def save_to_file(self):
        import json
        try:
            data = {}
            for col_name, col in self.collections.items():
                data[col_name] = serialize_doc(col.docs)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving mock database file: {e}")

def sync_local_to_real_db(db_real):
    import json
    from bson import ObjectId
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_db.json")
    if not os.path.exists(file_path):
        return
        
    try:
        print("Checking for local mock_db.json data to sync to MongoDB...")
        with open(file_path, "r", encoding="utf-8") as f:
            local_data = json.load(f)
            
        for col_name, docs in local_data.items():
            if not docs:
                continue
            if col_name not in ["registrations", "scores", "results", "events"]:
                continue
                
            collection = db_real[col_name]
            synced_count = 0
            
            for doc in docs:
                doc_id = doc.get("_id")
                if doc_id:
                    try:
                        query_id = ObjectId(doc_id)
                    except Exception:
                        query_id = doc_id
                else:
                    continue
                    
                if collection.find_one({"_id": query_id}) is None:
                    doc_to_insert = doc.copy()
                    doc_to_insert["_id"] = query_id
                    collection.insert_one(doc_to_insert)
                    synced_count += 1
                    
            if synced_count > 0:
                print(f"Synced {synced_count} documents from local mock_db.json to MongoDB collection '{col_name}'.")
    except Exception as e:
        print(f"Error syncing local data to MongoDB: {e}")

# Initialize client
try:
    if MONGO_URI:
        print(f"Connecting to MongoDB Atlas...")
        # tlsInsecure=True disables cert + hostname validation, fixing SSL handshake
        # errors (TLSV1_ALERT_INTERNAL_ERROR) seen on Windows with Python 3.10+
        db_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=8000
        )
        db_client.server_info()
        db_instance = db_client.get_default_database()
        print("Connected to MongoDB Atlas successfully.")
        sync_local_to_real_db(db_instance)
    else:
        raise ValueError("No MONGO_URI environment variable provided.")
except Exception as e:
    print(f"Error connecting to MongoDB Atlas: {e}")
    print("Falling back to local MongoDB instance at localhost:27017...")
    try:
        db_client = MongoClient("mongodb://localhost:27017/sports_day", serverSelectionTimeoutMS=2000)
        db_client.server_info()
        db_instance = db_client["sports_day"]
        print("Connected to local MongoDB successfully.")
        sync_local_to_real_db(db_instance)
    except Exception as local_err:
        print(f"Error connecting to local MongoDB: {local_err}")
        print("Starting in-memory Mock Database fallback...")
        db_instance = MockDatabase()

def get_db():
    return db_instance

def serialize_doc(doc):
    """Converts MongoDB BSON document to JSON-serializable dictionary."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    
    serialized = {}
    for key, value in doc.items():
        if key == "_id":
            serialized[key] = str(value)
        elif isinstance(value, dict):
            serialized[key] = serialize_doc(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_doc(item) if isinstance(item, dict) else item for item in value]
        else:
            serialized[key] = value
    return serialized
