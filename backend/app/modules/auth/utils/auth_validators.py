from app.shared.constants.regex_patterns import EMAIL_PATTERN, PASSWORD_PATTERN, USERNAME_PATTERN
from typing import Optional
import re

def validate_password_strength(password: str, username: str = None, email: str = None) -> Optional[str]:
    if len(password) < 8:
        return "Mật khẩu phải có ít nhất 8 ký tự"

    if not re.search(r'[A-Z]', password):
        return "Mật khẩu phải chứa ít nhất một chữ hoa"

    if not re.search(r'\d', password):
        return "Mật khẩu phải chứa ít nhất một số"

    if not re.search(r'[!@#$%^&*]', password):
        return "Mật khẩu phải chứa ít nhất một ký tự đặc biệt (!@#$%^&*)"

    common_passwords = [
        "Password123!", "Admin123!", "Qwerty123!", "Welcome123!",
        "password", "123456", "qwerty", "admin"
    ]
    if password.lower() in [p.lower() for p in common_passwords]:
        return "Mật khẩu quá phổ biến, vui lòng chọn mật khẩu mạnh hơn"

    if username and password == username:
        return "Mật khẩu không được trùng với tên đăng nhập"

    if email and password == email:
        return "Mật khẩu không được trùng với email"

    return None

def validate_username(username: str, email: str = None) -> Optional[str]:
    if len(username) < 3:
        return "Tên đăng nhập phải có ít nhất 3 ký tự"
    if len(username) > 20:
        return "Tên đăng nhập không được quá 20 ký tự"

    if not re.match(USERNAME_PATTERN, username):
        return "Tên đăng nhập không hợp lệ (chỉ chứa chữ, số, ., _, - và không bắt đầu/kết thúc bằng ký tự đặc biệt)"

    if email:
        local_part = email.split('@')[0]
        if username.lower() == local_part.lower():
             return "Tên đăng nhập không được giống hệt phần đầu của email"

    return None

def validate_email(email: str) -> Optional[str]:
    if not email or not email.strip():
        return "Email là bắt buộc"

    if len(email) > 254:
        return "Email quá dài (tối đa 254 ký tự)"

    if not re.match(EMAIL_PATTERN, email):
        return "Định dạng email không hợp lệ"

    return None