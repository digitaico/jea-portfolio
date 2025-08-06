#!/usr/bin/env python3
"""
SAFE Cleanup script to remove ONLY the transformation_history table from the public schema.
This script will:
1. Show you what it found (dry-run mode)
2. Ask for confirmation before deleting anything
3. Only target the specific transformation_history table we created
"""

from sqlalchemy import create_engine, text
from config import get_database_url
import sys

def cleanup_public_schema(dry_run=True):
    """Safely remove the transformation_history table from the public schema."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url, echo=False)
        
        with engine.connect() as connection:
            print("🔍 Checking for transformation_history table in public schema...")
            
            # Check if the table exists in public schema
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'transformation_history'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                print("⚠️  FOUND: transformation_history table in public schema")
                
                # Show table details for confirmation
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'transformation_history'
                    ORDER BY ordinal_position;
                """))
                
                columns = result.fetchall()
                print("   Table structure:")
                for col in columns:
                    print(f"     - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                
                if dry_run:
                    print("\n🔍 DRY RUN MODE: No changes will be made")
                    print("   To actually delete this table, run: python3 cleanup_public_schema.py --confirm")
                    return False
                else:
                    # Ask for final confirmation
                    response = input("\n❓ Are you SURE you want to delete the transformation_history table from public schema? (yes/no): ")
                    if response.lower() in ['yes', 'y']:
                        print("🗑️  Deleting transformation_history table from public schema...")
                        connection.execute(text("DROP TABLE IF EXISTS public.transformation_history CASCADE"))
                        connection.commit()
                        print("✅ Successfully removed transformation_history table from public schema")
                        return True
                    else:
                        print("❌ Deletion cancelled by user")
                        return False
            else:
                print("ℹ️  No transformation_history table found in public schema")
                return False
                
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def check_new_schema():
    """Check if the new image_processor schema and table exist."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url, echo=False)
        
        with engine.connect() as connection:
            print("\n🔍 Checking new image_processor schema...")
            
            # Check if schema exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.schemata 
                    WHERE schema_name = 'image_processor'
                );
            """))
            
            schema_exists = result.scalar()
            
            if schema_exists:
                print("✅ image_processor schema exists")
                
                # Check if the table exists in the new schema
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'image_processor' 
                        AND table_name = 'transformation_history'
                    );
                """))
                
                table_exists = result.scalar()
                
                if table_exists:
                    print("✅ transformation_history table exists in image_processor schema")
                    return True
                else:
                    print("⚠️  transformation_history table not found in image_processor schema")
                    return False
            else:
                print("⚠️  image_processor schema not found")
                return False
                
    except Exception as e:
        print(f"❌ Error checking new schema: {e}")
        return False

if __name__ == "__main__":
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        dry_run = False
    
    print("🛡️  SAFE CLEANUP SCRIPT - Image Processor Database")
    print("=" * 50)
    
    # First check the new schema
    new_schema_ok = check_new_schema()
    
    if not new_schema_ok:
        print("\n⚠️  WARNING: New schema not ready. Please run the application first to create the new schema.")
        sys.exit(1)
    
    # Then handle cleanup
    cleanup_public_schema(dry_run)
    
    print("\n✅ Cleanup script completed safely!") 