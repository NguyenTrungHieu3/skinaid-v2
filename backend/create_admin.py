#!/usr/bin/env python3
"""
SkinAid Admin User Creation Script
Creates an admin user in the database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from argon2 import PasswordHasher  # ← THAY ĐỔI: Dùng Argon2 thay vì bcrypt
import uuid
from datetime import datetime
import secrets
import string

import os
from dotenv import load_dotenv

# Try to load .env file from the parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'skinaid_db_v2'), # Pointing to the new schema DB
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '123456')
}
# Fallback logic if DATABASE_URL is preferred but components are missing
db_url = os.getenv('DATABASE_URL')
if db_url and 'skinaid_db_v2' in db_url:
    DB_CONFIG['database'] = 'skinaid_db_v2'

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def hash_password(password: str) -> str:
    """
    Hash password using Argon2 (SAME as application)
    """
    ph = PasswordHasher()  # ← THAY ĐỔI
    hashed = ph.hash(password)  # ← THAY ĐỔI
    return hashed


# ============================================================
# MAIN FUNCTION (giữ nguyên phần còn lại)
# ============================================================

def create_admin_user(
    email: str,
    username: str,
    password: str = None,
    full_name: str = None,
    auto_generate_password: bool = True
):
    """Create an admin user in the database"""
    
    if auto_generate_password or not password:
        password = generate_password(16)
        print(f"🔐 Generated secure password: {password}")
    
    # Hash the password (now using Argon2)
    hashed_password = hash_password(password)
    
    conn = None
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        conn.autocommit = False
        
        # 1. Create user
        print(f"👤 Creating user: {username} ({email})...")
        user_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO users (
                user_id, email, hashed_password, user_name, 
                token_version, is_active, is_verified, 
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id, email, user_name
        """, (
            user_id,
            email,
            hashed_password,
            username,
            0,
            True,
            True,
            datetime.now(),
            datetime.now()
        ))
        
        user_data = cursor.fetchone()
        print(f"✅ User created with ID: {user_data['user_id']}")
        
        # 2. Create user profile
        print("📝 Creating user profile...")
        
        cursor.execute("""
            INSERT INTO user_profiles (
                user_id, full_name, 
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s)
            RETURNING user_id
        """, (
            user_id,
            full_name or username,
            datetime.now(),
            datetime.now()
        ))
        
        profile_data = cursor.fetchone()
        print(f"✅ Profile created for user ID: {profile_data['user_id']}")
        
        # 3. Get admin role ID
        print("🔍 Finding admin role...")
        cursor.execute("""
            SELECT role_id, role_name 
            FROM roles 
            WHERE role_name = 'admin' AND is_active = true
        """)
        
        admin_role = cursor.fetchone()
        
        if not admin_role:
            raise Exception("❌ Admin role not found in database!")
        
        print(f"✅ Found admin role: {admin_role['role_name']}")
        
        # 4. Assign admin role to user
        print("👑 Assigning admin role...")
        cursor.execute("""
            INSERT INTO user_roles (
                user_id, role_id, assigned_at
            )
            VALUES (%s, %s, %s)
        """, (
            user_id,
            admin_role['role_id'],
            datetime.now()
        ))
        
        print("✅ Admin role assigned successfully!")
        
        # 5. Verify permissions
        cursor.execute("""
            SELECT COUNT(*) as permission_count
            FROM role_permissions rp
            WHERE rp.role_id = %s
        """, (admin_role['role_id'],))
        
        perm_count = cursor.fetchone()
        print(f"✅ Admin has {perm_count['permission_count']} permissions")
        
        conn.commit()
        print("\n" + "="*60)
        print("🎉 ADMIN USER CREATED SUCCESSFULLY!")
        print("="*60)
        
        result = {
            'user_id': user_id,
            'email': email,
            'username': username,
            'password': password,
            'full_name': full_name or username,
            'role': 'admin',
            'is_active': True,
            'is_verified': True
        }
        
        return result
        
    except psycopg2.IntegrityError as e:
        if conn:
            conn.rollback()
        print(f"\n❌ ERROR: User already exists or integrity constraint violated")
        print(f"Details: {str(e)}")
        raise
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        raise
        
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("\n🔌 Database connection closed")


def display_user_info(user_info: dict):
    """Display created user information"""
    print("\n" + "="*60)
    print("📋 ADMIN ACCOUNT CREDENTIALS")
    print("="*60)
    print(f"👤 User ID      : {user_info['user_id']}")
    print(f"📧 Email        : {user_info['email']}")
    print(f"🔑 Username     : {user_info['username']}")
    print(f"🔐 Password     : {user_info['password']}")
    print(f"👑 Role         : {user_info['role']}")
    print(f"📝 Full Name    : {user_info['full_name']}")
    print(f"✅ Active       : {user_info['is_active']}")
    print(f"✅ Verified     : {user_info['is_verified']}")
    print("="*60)
    print("\n⚠️  IMPORTANT: Save these credentials securely!")
    print("⚠️  The password will not be shown again!\n")


def interactive_create_admin():
    """Interactive mode to create admin user"""
    print("\n" + "="*60)
    print("🚀 SkinAid Admin User Creation Wizard")
    print("="*60 + "\n")
    
    email = input("📧 Enter admin email: ").strip()
    username = input("🔑 Enter admin username: ").strip()
    full_name = input("📝 Enter full name (optional, press Enter to skip): ").strip()
    
    print("\n🔐 Password Options:")
    print("1. Auto-generate secure password (Recommended)")
    print("2. Enter custom password")
    choice = input("Choose option (1 or 2): ").strip()
    
    password = None
    auto_gen = True
    
    if choice == "2":
        password = input("Enter password: ").strip()
        confirm_password = input("Confirm password: ").strip()
        
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return
        
        auto_gen = False
    
    print("\n" + "-"*60)
    print("📋 Please confirm:")
    print(f"   Email: {email}")
    print(f"   Username: {username}")
    print(f"   Full Name: {full_name or username}")
    print(f"   Password: {'Auto-generated' if auto_gen else 'Custom'}")
    print("-"*60)
    
    confirm = input("\n✅ Create admin user? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return
    
    try:
        user_info = create_admin_user(
            email=email,
            username=username,
            password=password,
            full_name=full_name if full_name else None,
            auto_generate_password=auto_gen
        )
        
        display_user_info(user_info)
        
    except Exception as e:
        print(f"\n❌ Failed to create admin user: {str(e)}")


if __name__ == "__main__":
    # Check if argon2-cffi is installed
    try:
        from argon2 import PasswordHasher
    except ImportError:
        print("❌ argon2-cffi is not installed!")
        print("📦 Install it with: pip install argon2-cffi")
        exit(1)
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 is not installed!")
        print("📦 Install it with: pip install psycopg2-binary")
        exit(1)
    
    interactive_create_admin()
