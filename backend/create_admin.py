"""
Script to create a default admin user
Run this script once to create an admin account for testing

Usage:
    python create_admin.py
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session_maker
from app.modules.auth.models.user import User
from app.modules.auth.models.roles import Role
from app.modules.auth.models.user_roles import UserRole
from app.core.Security.password import hash_password
from app.shared.role_permission_enum import RoleEnum
import uuid


async def create_admin_user():
    """Create a default admin user if it doesn't exist"""
    
    # Admin credentials
    ADMIN_USERNAME = "admin"
    ADMIN_EMAIL = "admin@skinaid.com"
    ADMIN_PASSWORD = "Admin@123"  # You should change this after first login
    
    print("Creating admin user...")
    print(f"Username: {ADMIN_USERNAME}")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")
    print()
    
    session_maker = get_session_maker()
    if not session_maker:
        print("❌ Database not configured!")
        return
    
    async with session_maker() as session:
        # Check or create admin role
        result = await session.execute(
            select(Role).where(Role.role_name == RoleEnum.Admin.value)
        )
        admin_role = result.scalar_one_or_none()
        
        if not admin_role:
            print("Creating admin role...")
            admin_role = Role(
                role_id=uuid.uuid4(),
                role_name=RoleEnum.Admin.value,
                description="Administrator role with full access",
                is_active=True
            )
            session.add(admin_role)
            await session.commit()
            await session.refresh(admin_role)
            print("✅ Admin role created")
        
        # Check if admin already exists
        result = await session.execute(
            select(User).where(
                (User.user_name == ADMIN_USERNAME) | (User.email == ADMIN_EMAIL)
            )
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"   Username: {existing_admin.user_name}")
            print(f"   Email: {existing_admin.email}")
            
            # Check if user has admin role
            result = await session.execute(
                select(UserRole).where(
                    (UserRole.user_id == existing_admin.user_id) &
                    (UserRole.role_id == admin_role.role_id)
                )
            )
            user_admin_role = result.scalar_one_or_none()
            
            if user_admin_role:
                print("\n✅ User already has admin role. No action needed.")
            else:
                # Add admin role to existing user
                print("\n🔧 Adding admin role to existing user...")
                user_role = UserRole(
                    user_id=existing_admin.user_id,
                    role_id=admin_role.role_id,
                    assigned_by=existing_admin.user_id
                )
                session.add(user_role)
                await session.commit()
                print("✅ Admin role added successfully!")
            return
        
        # Create new admin user
        admin_user = User(
            user_id=uuid.uuid4(),
            user_name=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            is_active=True,
            is_verified=True,
            is_deleted=False
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        # Assign admin role to user
        user_role = UserRole(
            user_id=admin_user.user_id,
            role_id=admin_role.role_id,
            assigned_by=admin_user.user_id
        )
        session.add(user_role)
        await session.commit()
        
        print("✅ Admin user created successfully!")
        print(f"\n📝 Login credentials:")
        print(f"   Username: {ADMIN_USERNAME}")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print(f"\n⚠️  Please change the password after first login!")
        print(f"\n🔗 You can now login at: http://localhost:5173/login")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
