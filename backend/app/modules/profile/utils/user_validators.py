from typing import Optional
from app.shared.constants.regex_patterns import PHONE_PATTERN
import re

def validate_phone_number(phone_number: str)-> Optional[str]:

    if phone_number is None:
        return None

    if not re.match(PHONE_PATTERN, phone_number):
        return "Invalid phone number format"

    return None

def validate_full_name(full_name: str) -> Optional[str]:
    if full_name is None:
        return None

    if not full_name or not full_name.strip():
        return "Full name is required"

    if len(full_name) < 2:
        return "Full name must be at least 2 characters"

    if len(full_name) > 100:
        return "Full name must not exceed 100 characters"

    if re.search(r'\d', full_name):
        return "Full name cannot contain numbers"

    if not re.match(r"^[a-zA-Z\s\-\'\u00C0-\u017F\u1E00-\u1EFF\u4E00-\u9FFF]+$", full_name):
        return "Full name contains invalid characters"

    return None

def validate_username(username: str) -> Optional[str]:
    if username is None:
        return "Username is required"

    if len(username) < 2:
        return "Username must be at least 2 characters"

    if len(username) > 50:
        return "Username must not exceed 50 characters"

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return "Username can only contain letters, numbers, underscore, and hyphen"

    return None