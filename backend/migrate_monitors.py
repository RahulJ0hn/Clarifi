#!/usr/bin/env python3
"""
Migration script to add item_name and item_type columns to monitors table
"""
import sqlite3
import os

def migrate_monitors():
    """Add item_name and item_type columns to monitors table"""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), 'ai_browser.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found. Please run the application first to create the database.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(monitors)")
        columns = [column[1] for column in cursor.fetchall()]
        
        changes_made = False
        
        # Add item_name column if it doesn't exist
        if 'item_name' not in columns:
            cursor.execute("ALTER TABLE monitors ADD COLUMN item_name VARCHAR")
            print("✅ Added item_name column")
            changes_made = True
        else:
            print("ℹ️  item_name column already exists")
        
        # Add item_type column if it doesn't exist
        if 'item_type' not in columns:
            cursor.execute("ALTER TABLE monitors ADD COLUMN item_type VARCHAR")
            print("✅ Added item_type column")
            changes_made = True
        else:
            print("ℹ️  item_type column already exists")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        if changes_made:
            print("✅ Database migration completed successfully!")
        else:
            print("ℹ️  No changes needed - columns already exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Running monitors table migration...")
    success = migrate_monitors()
    if success:
        print("🎉 Migration completed!")
    else:
        print("💥 Migration failed!") 