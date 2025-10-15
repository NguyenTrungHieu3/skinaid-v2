from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.core.config import settings
from typing import Dict, Any, Optional, Union
from fastapi import status, HTTPException
import hashlib

token_blacklist = set()

def is_token_blacklisted(jti: str) -> bool:

    return jti in token_blacklist

def blacklist_token(jti: str) -> None:

    token_blacklist.add(jti)

class JWTHandler:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self,
        subject: Union[str, int],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        current_time = datetime.now(timezone.utc)

        expire = (
            current_time + expires_delta
            if expires_delta
            else current_time + timedelta(minutes=self.access_token_expire_minutes)
        )

        jti = hashlib.sha256(f"{subject}{current_time}{self.secret_key}".encode()).hexdigest()[:32]

        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": current_time,
            "type": "access",
            "jti": jti
        }

        if additional_claims:
            payload.update(additional_claims)

        encoded_jwt = jwt.encode(payload, key=self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self,
        subject: Union[str, int],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        current_time = datetime.now(timezone.utc)

        expire = (
            current_time + expires_delta
            if expires_delta
            else current_time + timedelta(days=self.refresh_token_expire_days)
        )

        jti = hashlib.sha256(f"{subject}{current_time}{self.secret_key}refresh".encode()).hexdigest()[:32]

        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": current_time,
            "type": "refresh",
            "jti": jti
        }

        encoded_jwt = jwt.encode(payload, key=self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token=token, key=self.secret_key, algorithms=[self.algorithm])

            jti = payload.get("jti")
            if jti and is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or expired",
                headers={"WWW-Authenticate": "Bearer"}
            )