# MongoDB Setup Guide

## Error: MongoDB Connection Refused

If you see this error:
```
ServerSelectionTimeoutError: localhost:27017: [WinError 10061] No connection could be made
```

It means MongoDB is not running on your machine. Follow one of the solutions below.

---

## Solution 1: Start Local MongoDB (Windows)

### Step 1: Install MongoDB Community Edition

1. Download from: https://www.mongodb.com/try/download/community
2. Run the installer
3. Choose "Complete" installation
4. **Important**: Check "Install MongoDB as a Service"
5. Complete the installation

### Step 2: Start MongoDB Service

#### Method A: Using Services
1. Press `Windows + R`
2. Type `services.msc` and press Enter
3. Find "MongoDB" in the list
4. Right-click → Start
5. Set startup type to "Automatic" if you want it to start on boot

#### Method B: Using Command Prompt (as Administrator)
```cmd
net start MongoDB
```

### Step 3: Verify MongoDB is Running
```cmd
mongosh
```
If you see MongoDB shell, it's working! Type `exit` to leave.

### Step 4: Run Your Flask App
```bash
python app.py
```

---

## Solution 2: Use MongoDB Atlas (Cloud - Recommended for Beginners)

MongoDB Atlas is free and requires no local installation!

### Step 1: Create Account

1. Go to: https://www.mongodb.com/cloud/atlas/register
2. Sign up for free account
3. Verify your email

### Step 2: Create Free Cluster

1. Click "Build a Database"
2. Choose "FREE" (M0) tier
3. Select a cloud provider and region (choose closest to you)
4. Click "Create"

### Step 3: Create Database User

1. Go to "Database Access" (left sidebar)
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Username: `municipal_admin` (or any username)
5. Password: Create a strong password (save it!)
6. Click "Add User"

### Step 4: Whitelist IP Address

1. Go to "Network Access" (left sidebar)
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (for development)
   - Or add your specific IP for better security
4. Click "Confirm"

### Step 5: Get Connection String

1. Go to "Database" (left sidebar)
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Driver: Python, Version: 3.6 or later
5. Copy the connection string
   - It looks like: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

### Step 6: Update config.py

Replace `<username>` and `<password>` in the connection string:

```python
# In config.py
MONGODB_URI = 'mongodb+srv://municipal_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority'
```

Or set environment variable:
```bash
# Windows PowerShell
$env:MONGODB_URI="mongodb+srv://municipal_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"

# Windows CMD
set MONGODB_URI=mongodb+srv://municipal_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

### Step 7: Update Database Name (Optional)

If you want a specific database name, add it to the connection string:

```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/municipal_complaints?retryWrites=true&w=majority
```

### Step 8: Run Your Flask App
```bash
python app.py
```

---

## Quick Test: Check MongoDB Connection

Create a test file `test_mongo.py`:

```python
from pymongo import MongoClient

try:
    # Replace with your connection string
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✓ MongoDB connection successful!")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
```

Run it:
```bash
python test_mongo.py
```

---

## Troubleshooting

### Local MongoDB Issues

**Problem**: Service won't start
- **Solution**: Check if port 27017 is in use:
  ```cmd
  netstat -ano | findstr :27017
  ```

**Problem**: "MongoDB service not found"
- **Solution**: Reinstall MongoDB and ensure "Install as Service" is checked

**Problem**: Permission denied
- **Solution**: Run command prompt as Administrator

### Atlas Issues

**Problem**: Connection timeout
- **Solution**: Check IP whitelist in Network Access (allow 0.0.0.0/0 for testing)

**Problem**: Authentication failed
- **Solution**: Verify username/password in connection string (URL encode special characters)

**Problem**: Database name not found
- **Solution**: MongoDB Atlas creates databases automatically when you first write to them

---

## Which Should I Use?

### Use Local MongoDB if:
- ✅ You want full control
- ✅ You're comfortable with local services
- ✅ You need offline access
- ✅ You're doing development work

### Use MongoDB Atlas if:
- ✅ You want quick setup (5 minutes)
- ✅ You don't want to manage MongoDB
- ✅ You want cloud backup
- ✅ You're sharing the app with others
- ✅ You want free tier (512MB storage)

---

## Need Help?

- MongoDB Documentation: https://docs.mongodb.com/
- Atlas Help: https://docs.atlas.mongodb.com/
- Community Forum: https://www.mongodb.com/community/forums/

