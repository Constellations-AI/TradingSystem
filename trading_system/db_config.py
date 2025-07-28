"""
Database Configuration for Trading System
Handles persistent storage across deployments
"""
import os
import shutil
from pathlib import Path

def get_database_path() -> str:
    """Get the appropriate database path based on environment"""
    
    # Check if running on Railway (or other cloud platform)
    if os.getenv("RAILWAY_ENVIRONMENT_NAME") or os.getenv("RENDER"):
        # Use persistent volume path for production
        persistent_db_path = "/data/trading_system.db"
        local_db_path = "trading_system.db"
        
        # Create persistent directory if it doesn't exist
        os.makedirs("/data", exist_ok=True)
        
        # If persistent DB doesn't exist but local one does, copy it
        if not os.path.exists(persistent_db_path) and os.path.exists(local_db_path):
            print(f"🔄 Migrating database from {local_db_path} to {persistent_db_path}")
            shutil.copy2(local_db_path, persistent_db_path)
            print("✅ Database migration completed")
        
        return persistent_db_path
    else:
        # Use local path for development
        return "trading_system.db"

def backup_database():
    """Create a backup of the current database"""
    db_path = get_database_path()
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        shutil.copy2(db_path, backup_path)
        print(f"📦 Database backed up to {backup_path}")
        return backup_path
    return None

def restore_database(backup_path: str):
    """Restore database from backup"""
    db_path = get_database_path()
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, db_path)
        print(f"🔄 Database restored from {backup_path}")
        return True
    return False

# Export the database path for use by other modules
DATABASE_PATH = get_database_path()
print(f"📊 Using database path: {DATABASE_PATH}")