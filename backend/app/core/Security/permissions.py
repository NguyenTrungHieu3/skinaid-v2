from typing import List

def check_permission_match(user_permission: List[str], required_permission: str)-> bool: 
    """Check 1 Permission"""
    return required_permission in user_permission

def check_all_permission(user_permission: List[str], required_permissions: List[str]) -> bool: 
    """Check tất cả permissions - Cho endpoints cần nhiều quyền"""
    return all(perm in user_permission for perm in required_permissions)

def check_any_permission(user_permission: List[str], required_permissions: List[str]) -> bool: 
    """Check ít nhất 1 permission"""
    return any(perm in user_permission for perm in required_permissions )


