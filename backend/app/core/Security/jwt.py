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

    def _create_token(
        self,
        subject: Union[str, int],
        token_type: str,
        expires_delta: timedelta,
        token_version: int = 0,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, datetime]:
        current_time = datetime.now(timezone.utc)
        expire = current_time + expires_delta
        jti = hashlib.sha256(
            f"{subject}{current_time}{self.secret_key}{token_type}{token_version}".encode()
        ).hexdigest()[:32]

        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": current_time,
            "type": token_type,
            "jti": jti,
            "ver": token_version,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, key=self.secret_key, algorithm=self.algorithm)
        return token, jti, expire

    def create_token_pair(
        self,
        subject: Union[str, int],
        token_version: int = 0,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        access_token, access_jti, access_exp = self._create_token(
            subject=subject,
            token_type="access",
            expires_delta=timedelta(minutes=self.access_token_expire_minutes),
            token_version=token_version,
            additional_claims=additional_claims,
        )
        refresh_token, refresh_jti, refresh_exp = self._create_token(
            subject=subject,
            token_type="refresh",
            expires_delta=timedelta(days=self.refresh_token_expire_days),
            token_version=token_version,
            additional_claims={"access_jti": access_jti},
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_jti": access_jti,
            "refresh_jti": refresh_jti,
            "access_exp": access_exp,
            "refresh_exp": refresh_exp,
        }

    def create_access_token(
        self,
        subject: Union[str, int],
        token_version: int = 0,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        delta = expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        token, _, _ = self._create_token(
            subject=subject,
            token_type="access",
            expires_delta=delta,
            token_version=token_version,
            additional_claims=additional_claims,
        )
        return token

    def create_refresh_token(
        self,
        subject: Union[str, int],
        token_version: int = 0,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        delta = expires_delta or timedelta(days=self.refresh_token_expire_days)
        token, _, _ = self._create_token(
            subject=subject,
            token_type="refresh",
            expires_delta=delta,
            token_version=token_version,
        )
        return token

    def decode_token(
        self,
        token: str,
        verify_exp: bool = True,
    ) -> Dict[str, Any]:
        try:
            options = {"verify_exp": verify_exp} if not verify_exp else {}

            payload = jwt.decode(
                token=token,
                key=self.secret_key,
                algorithms=[self.algorithm],
                options=options,
            )

            return payload

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không hợp lệ hoặc đã hết hạn",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_token_type(self, payload: Dict[str, Any], expected_type: str) -> None:
        actual_type = payload.get("type")
        if actual_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Loại token không hợp lệ. Mong đợi '{expected_type}', nhận được '{actual_type}'",
                headers={"WWW-Authenticate": "Bearer"},
            )


jwt_handler = JWTHandler()
