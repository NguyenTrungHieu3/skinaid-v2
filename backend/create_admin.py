import asyncio
import sys
import os

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import select
from app.core.database import get_session_maker
from app.modules.auth.models.user import User
from app.modules.auth.models.roles import Role
from app.modules.auth.models.user_roles import UserRole
from app.core.Security.password import hash_password

async def create_admin_user():
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Check if user exists
        query = select(User).where(User.user_name == "admin")
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            print("Creating admin user...")
            hashed_pwd = hash_password("Admin123@")
            user = User(
                user_name="admin",
                email="admin@example.com", # Placeholder email
                hashed_password=hashed_pwd,
                is_active=True,
                is_verified=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"User 'admin' created with ID: {user.user_id}")
        else:
            print("User 'admin' already exists.")

        # Check if role exists
        query = select(Role).where(Role.role_name == "admin")
        result = await session.execute(query)
        role = result.scalar_one_or_none()

        if not role:
            print("Creating admin role...")
            role = Role(role_name="admin", description="Administrator role")
            session.add(role)
            await session.commit()
            await session.refresh(role)
            print(f"Role 'admin' created with ID: {role.role_id}")
        else:
            print("Role 'admin' already exists.")

        # --- Create Permissions ---
        from app.modules.auth.models.permissions import Permission
        from app.modules.auth.models.role_permissions import RolePermission

        permissions_to_create = [
            "read_system_logs",
            "manage_users",
            "manage_firstaid",
            "read_all_history",
            "upload_image",
            "ai_analyze",
            "read_logs"
        ]

        for perm_name in permissions_to_create:
            query = select(Permission).where(Permission.permission_name == perm_name)
            result = await session.execute(query)
            permission = result.scalar_one_or_none()

            if not permission:
                print(f"Creating permission '{perm_name}'...")
                permission = Permission(permission_name=perm_name, description=f"Permission to {perm_name.replace('_', ' ')}")
                session.add(permission)
                await session.commit()
                await session.refresh(permission)
            
            # Assign permission to role
            query = select(RolePermission).where(
                RolePermission.role_id == role.role_id,
                RolePermission.permission_id == permission.permission_id
            )
            result = await session.execute(query)
            role_perm = result.scalar_one_or_none()

            if not role_perm:
                print(f"Assigning permission '{perm_name}' to admin role...")
                role_perm = RolePermission(role_id=role.role_id, permission_id=permission.permission_id)
                session.add(role_perm)
                await session.commit()

        # Assign role to user
        query = select(UserRole).where(UserRole.user_id == user.user_id, UserRole.role_id == role.role_id)
        result = await session.execute(query)
        user_role = result.scalar_one_or_none()

        if not user_role:
            print("Assigning admin role to user...")
            user_role = UserRole(user_id=user.user_id, role_id=role.role_id)
            session.add(user_role)
            await session.commit()
            print("Admin role assigned.")
        else:
            print("User 'admin' already has 'admin' role.")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
