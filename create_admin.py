#!/usr/bin/env python3
"""
Create Admin User Script
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User, UserType

def create_admin_user():
    """Create or reset admin user"""
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        try:
            # Check if admin user already exists
            admin = db.session.query(User).filter_by(username="admin").first()
            
            if admin:
                print("Admin user already exists. Resetting password...")
                admin.set_password("admin123")
            else:
                print("Creating new admin user...")
                admin = User(
                    username="admin",
                    password="admin123",  # Required parameter
                    user_type=UserType.ADMIN,
                    email="admin@health.go.ug",
                    full_name="System Administrator",
                    organization="Ministry of Health Uganda",
                    position="System Administrator"
                )
                db.session.add(admin)
            
            db.session.commit()
            print("✅ Admin user ready:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Login at: http://127.0.0.1:5000")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()

if __name__ == "__main__":
    create_admin_user()
