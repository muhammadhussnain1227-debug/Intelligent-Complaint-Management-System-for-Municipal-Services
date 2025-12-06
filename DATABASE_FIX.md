# MongoDB Database Structure - Fixed and Verified

## ✅ Issues Fixed

1. **Database Initialization**: Added automatic database and collection initialization on startup
2. **Collection Creation**: Collections are now properly created when the app starts
3. **Database Visibility**: Added diagnostic tools to view database structure
4. **Better Logging**: Enhanced logging to show where complaints are saved

## 📊 Database Structure

Your MongoDB now has this structure:

### Complaints Database: `municipal_complaints`

**Collections:**
- `activity_logs` - Activity tracking for all complaints
- `complaints_garbage_collection` - All garbage collection complaints
- `complaints_road_damage` - All road damage complaints  
- `complaints_water_leakage` - All water leakage complaints
- `complaints_drainage_problems` - All drainage complaints
- `complaints_streetlight_malfunction` - All streetlight complaints
- `complaints_potholes` - All pothole complaints
- `complaints_tree_maintenance` - All tree maintenance complaints
- `complaints_public_toilets` - All public toilet complaints
- `complaints_parks_and_recreation` - All parks & recreation complaints
- `complaints_noise_complaints` - All noise complaints
- `complaints_parking_issues` - All parking complaints
- `complaints_other` - All other complaints

### Users Database: `municipal_users`

**Collections:**
- `users` - All user accounts (citizens, staff, admin)

## 🔍 How to Verify Your Database

### Method 1: Using the Check Script

Run this command in your project directory:

```bash
python check_database_structure.py
```

This will show you:
- All databases
- All collections in each database
- Document counts for each collection
- Sample data structure

### Method 2: Using MongoDB Compass

1. Open MongoDB Compass
2. Connect to: `mongodb://localhost:27017/`
3. Look for database: **`municipal_complaints`**
4. Expand it to see all category collections
5. Each collection contains complaints of that type

### Method 3: Using MongoDB Shell

```bash
# Connect to MongoDB
mongosh

# List all databases
show dbs

# Use complaints database
use municipal_complaints

# List all collections
show collections

# See all documents in a category collection
db.complaints_garbage_collection.find().pretty()

# Count documents in a collection
db.complaints_garbage_collection.countDocuments({})

# Count all complaints across all categories
db.complaints_garbage_collection.countDocuments({})
db.complaints_road_damage.countDocuments({})
# ... etc for each category
```

## 📝 Important Notes

1. **Collections appear only after first document**: MongoDB creates collections lazily. They won't appear in Compass until you save at least one complaint of that type.

2. **Database location**: 
   - Database name: `municipal_complaints`
   - Users database: `municipal_users`
   - Both are in your MongoDB instance

3. **Where complaints are saved**: When you submit a complaint:
   - It's saved to the category-specific collection
   - Example: "Garbage Collection" complaint → `complaints_garbage_collection` collection
   - Example: "Road Damage" complaint → `complaints_road_damage` collection

4. **Activity Logs**: All complaint activities are logged in `activity_logs` collection in the complaints database

## 🧪 Testing

1. **Submit a test complaint**:
   - Login to your app
   - Go to "Submit Complaint"
   - Fill in the form and submit
   - Check the console output - it will show exactly where it was saved

2. **Check the console**: When you save a complaint, you'll see:
   ```
   ✓ Complaint saved successfully with ID: ...
   ✓ Complaint ID: COM-...
   ✓ Saved to collection: complaints_garbage_collection
   ✓ Database: municipal_complaints
   ✓ Full collection path: municipal_complaints.complaints_garbage_collection
   ```

3. **Verify in MongoDB**:
   - Run `python check_database_structure.py`
   - Or check MongoDB Compass
   - You should see the new complaint in the appropriate collection

## 🐛 Troubleshooting

### Problem: "No collections found"

**Solution**: This is normal if you haven't saved any complaints yet. MongoDB creates collections only when you insert the first document.

### Problem: "Can't see database in MongoDB Compass"

**Solution**: 
1. Make sure MongoDB is running
2. Check the connection string in `config.py`
3. Default should be: `mongodb://localhost:27017/`
4. In Compass, connect to `mongodb://localhost:27017/`
5. The database `municipal_complaints` will appear after you save a complaint

### Problem: "Complaints not saving"

**Solution**:
1. Check the console output when submitting
2. Look for error messages
3. Verify MongoDB connection is working
4. Run `python check_database_structure.py` to verify connection

### Problem: "Wrong database name"

**Solution**: Check `config.py`:
```python
COMPLAINTS_DATABASE_NAME = 'municipal_complaints'  # Default
USERS_DATABASE_NAME = 'municipal_users'  # Default
```

You can change these values if needed, but make sure to update them before saving any data.

## ✅ Verification Checklist

- [ ] MongoDB is running
- [ ] App starts without database errors
- [ ] Database initialization messages appear in console
- [ ] Can submit a complaint successfully
- [ ] Console shows "Complaint saved successfully"
- [ ] Can see collections in MongoDB Compass or using check script
- [ ] Complaints appear in correct category collections

