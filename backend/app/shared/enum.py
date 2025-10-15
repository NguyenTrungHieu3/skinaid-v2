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
    READ_FIRSTAID = "read_firsaid"
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
    # User management
    PermissionEnum.CREATE_USER: "Create new user accounts",
    PermissionEnum.READ_USER: "View user information",
    PermissionEnum.UPDATE_USER: "Modify user data",
    PermissionEnum.DELETE_USER: "Delete user accounts",
    
    # First-aid content
    PermissionEnum.CREATE_FIRSTAID: "Create first-aid guides",
    PermissionEnum.READ_FIRSTAID: "View first-aid guides",
    PermissionEnum.UPDATE_FIRSTAID: "Modify first-aid guides",
    PermissionEnum.DELETE_FIRSTAID: "Delete first-aid guides",
    
    # AI & Upload
    PermissionEnum.UPLOAD_IMAGE: "Upload wound images",
    PermissionEnum.AI_ANALYZE: "Request AI analysis",
    
    # History
    PermissionEnum.READ_OWN_HISTORY: "View own wound history",
    PermissionEnum.READ_ALL_HISTORY: "View all users' history",
    
    # System
    PermissionEnum.READ_SYSTEM_LOGS: "View system logs",
    PermissionEnum.MANAGE_ROLES: "Manage roles and role assignments",
}
