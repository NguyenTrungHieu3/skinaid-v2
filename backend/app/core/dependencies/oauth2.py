from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    auto_error=False,
)
