from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession 
from app.core.database import get_session
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from app.modules.auth.models.user import User
from app.core.security import JWTHandler
from sqlmodel import text
jwt = JWTHandler()
get_db = get_session

async def get_token(authorization: Optional[str] = Header(None)) -> str:
    if authorization is None: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split(" ")[1]
    return token 

async def get_current_user(token: Optional[str] = Depends(get_token) ,db: AsyncSession = Depends(get_db)) -> User:
    try: 
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization token missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        payload = jwt.verify_token(token) 
        
        user_id = payload.get("sub")
        if user_id is None: 
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        select_sql = text("SELECT * FROM users WHERE id = :id")
        params = {
            "id": user_id 
        }

        result = await db.execute(select_sql, params)
        user_row = result.mappings().first()

        if user_row is None: 
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Convert row to User object
        user_data = dict(user_row)
        user = User.model_validate(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user