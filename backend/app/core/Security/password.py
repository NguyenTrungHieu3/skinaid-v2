from passlib.context import CryptContext
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# print(hash_password("pass_Word123!"))

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)