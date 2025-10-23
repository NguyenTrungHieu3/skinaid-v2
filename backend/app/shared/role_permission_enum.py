from enum import Enum

class RoleEnum(str, Enum): 
    Admin = "admin"
    User = "user"

class PermissionEnum(str, Enum):
    
    #User Management Permissions 
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"

    #First-Aid Content Permissions
    CREATE_FIRSTAID = "create_firstaid"
    READ_FIRSTAID = "read_firstaid"
    UPDATE_FIRSTAID = "update_firstaid"
    DELETE_FIRSTAID = "delete_firstaid"

    #AI & Upload Permissions
    UPLOAD_IMAGE = "upload_image"
    AI_ANALYZE = "ai_analyze"

    #History Permissions    
    READ_OWN_HISTORY = "read_own_history"
    READ_ALL_HISTORY = "read_all_history"  # Admin only
    
    #System Permissions    
    READ_SYSTEM_LOGS = "read_system_logs"
    MANAGE_ROLES = "manage_roles"

class PermissionCategory(str, Enum):
    USER_MANAGEMENT = "user_management"
    AI = "ai"
    SYSTEM = "system"
    CONTENT = "content"

ROLE_PERMISSIONS = {
    RoleEnum.Admin: [
        PermissionEnum.CREATE_USER,
        PermissionEnum.READ_USER,
        PermissionEnum.UPDATE_USER,
        PermissionEnum.DELETE_USER,
        PermissionEnum.CREATE_FIRSTAID,
        PermissionEnum.READ_FIRSTAID,
        PermissionEnum.UPDATE_FIRSTAID,
        PermissionEnum.DELETE_FIRSTAID,
        PermissionEnum.UPLOAD_IMAGE,
        PermissionEnum.AI_ANALYZE,
        PermissionEnum.READ_OWN_HISTORY,
        PermissionEnum.READ_ALL_HISTORY,
        PermissionEnum.READ_SYSTEM_LOGS,
        PermissionEnum.MANAGE_ROLES,
    ], 

    RoleEnum.User: [
        PermissionEnum.READ_FIRSTAID, 
        PermissionEnum.UPLOAD_IMAGE,
        PermissionEnum.AI_ANALYZE, 
        PermissionEnum.READ_OWN_HISTORY, 

    ]
}

PERMISSION_DESCRIPTIONS ={
    PermissionEnum.CREATE_USER: "Create new user accounts",
    PermissionEnum.READ_USER: "View user information",
    PermissionEnum.UPDATE_USER: "Modify user data",
    PermissionEnum.DELETE_USER: "Delete user accounts",
    
    PermissionEnum.CREATE_FIRSTAID: "Create first-aid guides",
    PermissionEnum.READ_FIRSTAID: "View first-aid guides",
    PermissionEnum.UPDATE_FIRSTAID: "Modify first-aid guides",
    PermissionEnum.DELETE_FIRSTAID: "Delete first-aid guides",
    
    PermissionEnum.UPLOAD_IMAGE: "Upload wound images",
    PermissionEnum.AI_ANALYZE: "Request AI analysis",
    
    PermissionEnum.READ_OWN_HISTORY: "View own wound history",
    PermissionEnum.READ_ALL_HISTORY: "View all users' history",
    
    PermissionEnum.READ_SYSTEM_LOGS: "View system logs",
    PermissionEnum.MANAGE_ROLES: "Manage roles and role assignments",
}

GUEST_ALLOWED_FEATURES = [
    "read_firstaid",
    "upload_image", 
    "ai_analyze",
]

GUEST_LIMITS = {
    "max_uploads_per_session": 3,
    "max_analyses_per_session": 3, 
    "session_duration_minutes": 60, 
    "max_file_size_mb": 5,
}

def get_permission_for_role(role: RoleEnum) -> list[PermissionEnum]: 
    return ROLE_PERMISSIONS.get(role, [])

def get_permission_description(permission: PermissionEnum) -> str:
    return PERMISSION_DESCRIPTIONS.get(permission, "No description available")

def is_guest_feature_allowed(feature: str) -> bool:
    """kiểm tra user có permission đó không """
    return feature in GUEST_ALLOWED_FEATURES


# print(RoleEnum.Admin)  
# print(RoleEnum.User)   

# print(PermissionEnum.AI_ANALYZE) 

# print(len(ROLE_PERMISSIONS[RoleEnum.Admin]))  
# print(len(ROLE_PERMISSIONS[RoleEnum.User]))  

# print(GUEST_LIMITS["max_analyses_per_session"])  