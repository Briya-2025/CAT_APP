#!/usr/bin/env python
"""
Migration script to move data from SQLite to PostgreSQL
Run this script to migrate your existing SQLite data to PostgreSQL
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uca_project.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.apps import apps

def migrate_to_postgresql():
    """
    Migrate data from SQLite to PostgreSQL
    """
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    
    # Step 1: Create a backup of SQLite database
    print("📦 Creating SQLite backup...")
    import shutil
    from pathlib import Path
    
    BASE_DIR = Path(__file__).resolve().parent
    sqlite_db = BASE_DIR / 'db.sqlite3'
    backup_db = BASE_DIR / 'db_backup.sqlite3'
    
    if sqlite_db.exists():
        shutil.copy2(sqlite_db, backup_db)
        print(f"✅ SQLite backup created: {backup_db}")
    else:
        print("⚠️ No SQLite database found. Skipping backup.")
    
    # Step 2: Switch to production settings (PostgreSQL)
    print("🔧 Switching to PostgreSQL settings...")
    os.environ['DJANGO_SETTINGS_MODULE'] = 'uca_project.settings_production'
    django.setup()
    
    # Step 3: Create PostgreSQL database tables
    print("🗄️ Creating PostgreSQL database tables...")
    call_command('migrate', verbosity=2)
    
    # Step 4: Load data from SQLite backup if it exists
    if backup_db.exists():
        print("📥 Loading data from SQLite backup...")
        try:
            # Use Django's loaddata command to load fixtures
            # First, we need to dump data from SQLite
            print("📤 Dumping data from SQLite...")
            call_command('dumpdata', '--natural-foreign', '--natural-primary', 
                        output='data_fixture.json', verbosity=2)
            
            print("📥 Loading data into PostgreSQL...")
            call_command('loaddata', 'data_fixture.json', verbosity=2)
            
            # Clean up fixture file
            os.remove('data_fixture.json')
            print("✅ Data migration completed!")
            
        except Exception as e:
            print(f"❌ Error during data migration: {e}")
            print("💡 You may need to manually migrate data or start fresh.")
    else:
        print("ℹ️ No existing data to migrate. PostgreSQL database is ready for new data.")
    
    # Step 5: Verify migration
    print("🧪 Verifying PostgreSQL connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL connection successful: {version}")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Step 6: Show database info
    print("\n📊 Migration Summary:")
    print("=" * 50)
    
    # Count records in each table
    for model in apps.get_models():
        try:
            count = model.objects.count()
            print(f"{model._meta.label}: {count} records")
        except Exception as e:
            print(f"{model._meta.label}: Error counting records - {e}")
    
    print("=" * 50)
    print("✅ Migration to PostgreSQL completed successfully!")
    print("\n🔧 Next steps:")
    print("1. Update your GitHub secrets with the new DATABASE_URL")
    print("2. Test your application with PostgreSQL")
    print("3. Remove SQLite backup file when you're confident everything works")
    
    return True

if __name__ == '__main__':
    success = migrate_to_postgresql()
    if success:
        print("\n🎉 Migration completed successfully!")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
