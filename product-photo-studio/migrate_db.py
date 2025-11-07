"""
Database migration script to add GuestUsage table
Run this once after pulling the latest code:
  python migrate_db.py
"""

from app import app, db

def migrate():
    with app.app_context():
        # Create all tables (will skip existing ones)
        db.create_all()
        print("✅ Database migration complete! All tables created.")
        print("   - User table: ✓")
        print("   - Generation table: ✓")
        print("   - MobileUploadToken table: ✓")
        print("   - GuestUsage table: ✓ (NEW)")

if __name__ == "__main__":
    migrate()
