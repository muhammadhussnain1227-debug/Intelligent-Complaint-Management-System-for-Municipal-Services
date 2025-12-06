"""
Check Admin User in Database
This script verifies the admin user exists and has correct role
"""
from pymongo import MongoClient
from config import Config
import bcrypt

def check_admin_user():
    """Check admin user in database"""
    
    print("="*60)
    print("Admin User Check")
    print("="*60)
    
    try:
        client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[Config.DATABASE_NAME]
        client.admin.command('ping')
        
        print("\n✓ Connected to MongoDB")
        
        # Find admin user
        admin_user = db.users.find_one({'email': 'admin@municipal.gov'})
        
        if admin_user:
            print("\n✓ Admin user found:")
            print(f"   Email: {admin_user.get('email')}")
            print(f"   Name: {admin_user.get('name')}")
            print(f"   Role: {admin_user.get('role')}")
            print(f"   Active: {admin_user.get('is_active', True)}")
            print(f"   Created: {admin_user.get('created_at')}")
            
            # Test password
            test_password = 'admin123'
            try:
                password_match = bcrypt.checkpw(test_password.encode('utf-8'), admin_user['password'])
                print(f"\n   Password check ('admin123'): {'✓ Match' if password_match else '✗ No Match'}")
            except Exception as e:
                print(f"\n   ✗ Password check error: {e}")
            
            # Check if role is admin
            if admin_user.get('role') != 'admin':
                print(f"\n⚠️  WARNING: User role is '{admin_user.get('role')}' but should be 'admin'")
                print("\nFixing role...")
                db.users.update_one(
                    {'_id': admin_user['_id']},
                    {'$set': {'role': 'admin'}}
                )
                print("✓ Role updated to 'admin'")
            else:
                print("\n✓ Role is correctly set to 'admin'")
                
        else:
            print("\n✗ Admin user NOT found!")
            print("\nCreating admin user...")
            
            admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            from datetime import datetime
            result = db.users.insert_one({
                'name': 'System Administrator',
                'email': 'admin@municipal.gov',
                'phone': '0000000000',
                'password': admin_password,
                'role': 'admin',
                'created_at': datetime.utcnow(),
                'is_active': True,
                'profile': {}
            })
            
            if result.inserted_id:
                print("✓ Admin user created successfully")
                print("   Email: admin@municipal.gov")
                print("   Password: admin123")
            else:
                print("✗ Failed to create admin user")
        
        # List all users
        all_users = list(db.users.find({}, {'email': 1, 'role': 1, 'name': 1}))
        print(f"\n📊 All users in database ({len(all_users)}):")
        for user in all_users:
            print(f"   - {user.get('email')}: {user.get('role')} ({user.get('name')})")
        
        client.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_admin_user()

