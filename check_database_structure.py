"""
Database Structure Checker
This script helps you verify the MongoDB database structure and see all collections.
"""
from pymongo import MongoClient
from config import Config
import sys

def check_database_structure():
    """Check and display MongoDB database structure"""
    print("="*70)
    print("MongoDB Database Structure Checker")
    print("="*70)
    print()
    
    try:
        # Connect to MongoDB
        client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✓ Connected to MongoDB successfully")
        print()
    except Exception as e:
        print(f"✗ MongoDB connection error: {e}")
        print("\nPlease make sure MongoDB is running:")
        print("  - Windows: net start MongoDB")
        print("  - Or check MongoDB service in Services")
        return
    
    try:
        # Check Complaints Database
        complaints_db = client[Config.COMPLAINTS_DATABASE_NAME]
        print(f"📊 COMPLAINTS DATABASE: '{Config.COMPLAINTS_DATABASE_NAME}'")
        print("-" * 70)
        
        collections = complaints_db.list_collection_names()
        if collections:
            print(f"   Found {len(collections)} collection(s):\n")
            for coll_name in sorted(collections):
                count = complaints_db[coll_name].count_documents({})
                print(f"   📁 Collection: {coll_name}")
                print(f"      Documents: {count}")
                
                # Show sample document if exists
                if count > 0:
                    sample = complaints_db[coll_name].find_one()
                    if sample:
                        print(f"      Sample fields: {list(sample.keys())[:10]}")
                print()
        else:
            print("   ⚠️  No collections found!")
            print("   ℹ️  Collections will be created when you save your first complaint.")
            print()
        
        # List all databases to help user find their data
        print(f"\n💡 All databases in MongoDB:")
        print("-" * 70)
        all_databases = client.list_database_names()
        for db_name in sorted(all_databases):
            if db_name not in ['admin', 'config', 'local']:
                db = client[db_name]
                colls = db.list_collection_names()
                print(f"   📦 {db_name}: {len(colls)} collection(s)")
                if colls:
                    for coll in colls[:5]:  # Show first 5 collections
                        count = db[coll].count_documents({})
                        print(f"      - {coll}: {count} documents")
                    if len(colls) > 5:
                        print(f"      ... and {len(colls) - 5} more")
        print()
        
        # Check Users Database
        users_db = client[Config.USERS_DATABASE_NAME]
        print(f"👥 USERS DATABASE: '{Config.USERS_DATABASE_NAME}'")
        print("-" * 70)
        
        users_collections = users_db.list_collection_names()
        if users_collections:
            print(f"   Found {len(users_collections)} collection(s):\n")
            for coll_name in sorted(users_collections):
                count = users_db[coll_name].count_documents({})
                print(f"   📁 Collection: {coll_name}")
                print(f"      Documents: {count}\n")
        else:
            print("   ⚠️  No collections found!")
            print()
        
        print("="*70)
        print("\n✅ Check complete!")
        print("\n📝 Notes:")
        print("   - Category-specific collections are named: complaints_{category_name}")
        print("   - Example: complaints_garbage_collection, complaints_road_damage")
        print("   - Collections appear only after first document is inserted")
        print("   - Use MongoDB Compass to view data visually")
        print()
        
    except Exception as e:
        print(f"✗ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_database_structure()

