from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.core.config import settings
from typing import Dict, Any, Optional, Union, Tuple
from fastapi import HTTPException, status
import hashlib


class JWTHandler:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_token_pair(
        self, 
        subject: Union[str, int], 
        token_version: int = 0, 
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]: 
        """
        Create access + refresh token pair with family tracking
        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "access_jti": "...",
                "refresh_jti": "...",
                "access_exp": datetime,
                "refresh_exp": datetime
            }
        """
        current_time = datetime.now(timezone.utc)

        #create access token 
        access_exp = current_time + timedelta(minutes=self.access_token_expire_minutes)
        access_jti = hashlib.sha256(
            f"{subject}{current_time}{self.secret_key}access{token_version}".encode()
        ).hexdigest()[:32]
        
        access_payload ={
            "sub": str(subject), 
            "exp": access_exp, 
            "iat": current_time, 
            "type": "access", 
            "jti": access_jti, 
            "ver": token_version
        }

        if additional_claims: 
            access_payload.update(additional_claims)
        
        access_token = jwt.encode(access_payload, key=self.secret_key, algorithm=self.algorithm)

        #create refresh token
        refresh_exp = current_time + timedelta(days=self.refresh_token_expire_days)
        refresh_jti = hashlib.sha256(
            f"{subject}{current_time}{self.secret_key}refresh{token_version}".encode()
        ).hexdigest()[:32]

        refresh_payload = {
            "sub": str(subject), 
            "exp": refresh_exp, 
            "iat": current_time, 
            "type": "refresh", 
            "jti": refresh_jti, 
            "ver": token_version, 
            "access_jti": access_jti
        }

        refresh_token = jwt.encode(refresh_payload, key=self.secret_key, algorithm=self.algorithm)

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token, 
            "access_jti": access_jti, 
            "refresh_jti": refresh_jti, 
            "access_exp": access_exp, 
            "refresh_exp": refresh_exp
        }

    def create_access_token(
        self,
        subject: Union[str, int],
        token_version: int = 0, 
        expires_delta: Optional[timedelta] = None, 
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Tạo access token độc lập cho refresh endpoint 
        """
        current_time = datetime.now(timezone.utc)

        expire = (
            current_time + expires_delta
            if expires_delta
            else current_time + timedelta(minutes=self.access_token_expire_minutes)
        )

        jti = hashlib.sha256(
            f"{subject}{current_time}{self.secret_key}{token_version}".encode()
        ).hexdigest()[:32]

        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": current_time,
            "type": "access",
            "jti": jti,
            "ver": token_version
        }

        if additional_claims: 
            payload.update(additional_claims)

        return jwt.encode(payload, key=self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        subject: Union[str, int],
        token_version: int = 0, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Tạo refresh token độc lập 
        """
        current_time = datetime.now(timezone.utc)

        expire = (
            current_time + expires_delta
            if expires_delta
            else current_time + timedelta(days=self.refresh_token_expire_days)
        )

        jti = hashlib.sha256(
            f"{subject}{current_time}{self.secret_key}refresh{token_version}".encode()
        ).hexdigest()[:32]

        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": current_time,
            "type": "refresh",
            "jti": jti,
            "ver": token_version
        }

        return jwt.encode(payload, key=self.secret_key, algorithm=self.algorithm)

    def decode_token(
        self,
        token: str,
        verify_exp: bool = True
    ) -> Dict[str, Any]:
        """
        Decode JWT token
        """
        try:
            options = {"verify_exp": verify_exp} if not verify_exp else {}
            
            payload = jwt.decode(
                token=token,
                key=self.secret_key,
                algorithms=[self.algorithm],
                options=options
            )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_token_type(self, payload: Dict[str, Any], expected_type: str) -> None:
        """
        Verify token type 
        """
        actual_type = payload.get("type")
        if actual_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected '{expected_type}', got '{actual_type}'",
                headers={"WWW-Authenticate": "Bearer"},
            )


jwt_handler = JWTHandler()