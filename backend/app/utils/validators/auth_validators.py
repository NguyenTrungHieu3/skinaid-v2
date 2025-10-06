from app.utils.constants.regex_patterns import EMAIL_PATTERN, PASSWORD_PATTERN 
from typing import Optional
import re

def validate_password_strength(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters long"
        
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    
    if not re.search(r'\d', password):
        return "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*]', password):
        return "Password must contain at least one special character (!@#$%^&*)"
    
    common_passwords = [
        "Password123!", "Admin123!", "Qwerty123!", "Welcome123!",
        "password", "123456", "qwerty", "admin"
    ]
    if password.lower() in [p.lower() for p in common_passwords]:
        return "Password is too common, please choose a sronger password"
    
    return None
    
def validate_email(email: str) -> Optional[str]: 
    """Validate email format with detailed error messages."""
    if not email or not email.strip():
        return "Email is required"
    
    if len(email) > 254:
        return "Email is too long (maximum 254 characters)"
    
    if not re.match(EMAIL_PATTERN, email): 
        return "Invalid email format"
    
    return None 
    
