import asyncio
import sys
import os

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import select
from app.core.database import get_session_maker
from app.modules.auth.models.roles import Role

async def list_roles():
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Query all roles
        query = select(Role)
        result = await session.execute(query)
        roles = result.scalars().all()
        
        if roles:
            print("Existing roles in database:")
            for role in roles:
                print(f"  - {role.role_name} (ID: {role.role_id}, Description: {role.description})")
        else:
            print("No roles found in database!")
        
        print(f"\nTotal roles: {len(roles)}")

if __name__ == "__main__":
    asyncio.run(list_roles())
