#!/usr/bin/env python3
"""
List All Users Script
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User

def list_all_users():
    """List all users in the system"""
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        try:
            users = db.session.query(User).all()
            
            if not users:
                print("No users found in the system.")
                return
            
            print("🚀 Current Users in MOH MNCAH Dashboard:")
            print("=" * 60)
            
            for user in users:
                print(f"👤 Username: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   Full Name: {user.full_name}")
                print(f"   Type: {user.user_type.value}")
                print(f"   Status: {user.status.value}")
                print(f"   Organization: {user.organization}")
                print(f"   Created: {user.created_at}")
                print("-" * 60)
            
            print("\n✅ Ready to login at: http://127.0.0.1:5000")
            print("💡 Known credentials:")
            print("   - admin / admin123 (Admin user)")
            print("   - isaac / isaac (Admin user)")  
            print("   - stakeholder / stakeholder123 (Stakeholder user)")
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")

if __name__ == "__main__":
    list_all_users()
