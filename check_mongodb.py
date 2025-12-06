"""
Check MongoDB Connection Status
This script helps you verify your MongoDB connection settings
"""
import os
from pymongo import MongoClient
from config import Config

def check_mongodb_connection():
    """Check and display MongoDB connection information"""
    
    print("="*60)
    print("MongoDB Connection Check")
    print("="*60)
    
    # Get connection details
    mongodb_uri = os.environ.get('MONGODB_URI') or Config.MONGODB_URI
    database_name = os.environ.get('DATABASE_NAME') or Config.DATABASE_NAME
    
    print(f"\n📋 Connection Details:")
    print(f"   URI: {mongodb_uri.replace('mongodb://', 'mongodb://***').replace('mongodb+srv://', 'mongodb+srv://***')}")
    print(f"   Database: {database_name}")
    
    # Check environment variables
    print(f"\n🔍 Environment Variables:")
    if os.environ.get('MONGODB_URI'):
        print(f"   ✓ MONGODB_URI is set (from environment)")
    else:
        print(f"   ✗ MONGODB_URI not set (using default from config.py)")
    
    if os.environ.get('DATABASE_NAME'):
        print(f"   ✓ DATABASE_NAME is set (from environment)")
    else:
        print(f"   ✗ DATABASE_NAME not set (using default from config.py)")
    
    # Try to connect
    print(f"\n🔌 Attempting Connection...")
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        
        print("   ✓ Connection Successful!")
        
        # Get database info
        db = client[database_name]
        
        # List collections
        collections = db.list_collection_names()
        
        print(f"\n📊 Database Information:")
        print(f"   Database: {database_name}")
        print(f"   Collections: {len(collections)}")
        
        if collections:
            print(f"\n   Collections found:")
            for collection in collections:
                count = db[collection].count_documents({})
                print(f"     - {collection}: {count} documents")
        else:
            print(f"   (No collections yet - database is empty)")
        
        # Get server info
        server_info = client.server_info()
        print(f"\n🖥️  MongoDB Server:")
        print(f"   Version: {server_info.get('version', 'Unknown')}")
        
        # Check if it's Atlas
        if 'atlas' in mongodb_uri.lower() or 'mongodb+srv' in mongodb_uri:
            print(f"   Type: MongoDB Atlas (Cloud)")
        else:
            print(f"   Type: Local MongoDB")
        
        client.close()
        print("\n✅ MongoDB is ready to use!")
        return True
        
    except Exception as e:
        print(f"   ✗ Connection Failed!")
        print(f"\n❌ Error: {str(e)}")
        
        print("\n" + "="*60)
        print("Troubleshooting Steps:")
        print("="*60)
        
        if 'localhost' in mongodb_uri or '127.0.0.1' in mongodb_uri:
            print("\n🔧 For Local MongoDB:")
            print("   1. Check if MongoDB service is running:")
            print("      Windows: Open Services (services.msc) and look for 'MongoDB'")
            print("      Or run: net start MongoDB")
            print("   2. Verify MongoDB is installed:")
            print("      Run: mongod --version")
            print("   3. Check if port 27017 is available")
        else:
            print("\n🔧 For MongoDB Atlas:")
            print("   1. Verify your connection string is correct")
            print("   2. Check if your IP is whitelisted in Atlas")
            print("   3. Verify your username and password")
            print("   4. Make sure your cluster is running")
        
        print("\n📖 For more help, see: MONGODB_SETUP.md")
        return False

if __name__ == '__main__':
    check_mongodb_connection()

