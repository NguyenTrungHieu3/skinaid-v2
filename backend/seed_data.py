"""
Seed data script - Chạy khi khởi động backend lần đầu
Tạo admin user, roles, permissions và dữ liệu firstaid mẫu
"""
import asyncio
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import select
from app.core.database import get_session_maker
from app.modules.auth.models.user import User
from app.modules.auth.models.roles import Role
from app.modules.auth.models.user_roles import UserRole
from app.modules.auth.models.permissions import Permission
from app.modules.auth.models.role_permissions import RolePermission
from app.modules.firstaid.models.firstaid_guide import FirstAidGuide
from app.core.Security.password import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== PERMISSIONS DATA ====================
PERMISSIONS_DATA = [
    {"permission_name": "create_user", "description": "Create new user accounts"},
    {"permission_name": "read_user", "description": "View user information"},
    {"permission_name": "update_user", "description": "Modify user data"},
    {"permission_name": "delete_user", "description": "Delete user accounts"},
    {"permission_name": "create_firstaid", "description": "Create first-aid guides"},
    {"permission_name": "read_firstaid", "description": "View first-aid guides"},
    {"permission_name": "update_firstaid", "description": "Modify first-aid guides"},
    {"permission_name": "delete_firstaid", "description": "Delete first-aid guides"},
    {"permission_name": "upload_image", "description": "Upload wound images"},
    {"permission_name": "ai_analyze", "description": "Request AI analysis"},
    {"permission_name": "read_own_history", "description": "View own wound history"},
    {"permission_name": "read_all_history", "description": "View all users history"},
    {"permission_name": "read_system_logs", "description": "View system logs"},
    {"permission_name": "manage_roles", "description": "Manage roles and role assignments"},
    {"permission_name": "manage_users", "description": "Permission to manage users"},
    {"permission_name": "manage_firstaid", "description": "Permission to manage firstaid"},
    {"permission_name": "read_logs", "description": "Permission to read logs"},
]

# Admin có tất cả permissions
ADMIN_PERMISSIONS = [p["permission_name"] for p in PERMISSIONS_DATA]

# User chỉ có một số permissions cơ bản
USER_PERMISSIONS = ["read_firstaid", "upload_image", "ai_analyze", "read_own_history"]

# ==================== FIRSTAID DATA ====================
FIRSTAID_GUIDES_DATA = [
    # ============ BURN GUIDES ============
    {
        "wound_type": "burn",
        "severity": "mild",
        "sub_type": None,
        "title": "First Aid for Mild Burns",
        "description": "Basic treatment for first-degree burns with no blisters",
        "steps": [
            "Cool the burn under running water for 10-20 minutes",
            "Apply aloe vera gel or burn cream",
            "Cover with sterile gauze if needed",
            "Take over-the-counter pain reliever"
        ],
        "warnings": [
            "Do not apply ice directly",
            "Do not use butter or oil"
        ],
        "dos": [
            "Keep the area clean",
            "Monitor for signs of infection"
        ],
        "donts": [
            "Do not pop any blisters",
            "Do not apply home remedies without medical advice"
        ],
        "estimated_healing_time": "3-7 days",
        "supplies_needed": [
            "Clean water",
            "Aloe vera gel",
            "Sterile gauze",
            "Pain reliever"
        ]
    },
    {
        "wound_type": "burn",
        "severity": "moderate",
        "sub_type": "blister",
        "title": "First Aid for Burns with Blisters",
        "description": "Special care for second-degree burns with intact blisters",
        "steps": [
            "Cool the burn gently with clean water",
            "Do NOT pop or puncture blisters",
            "Cover loosely with sterile non-stick dressing",
            "Elevate if possible",
            "Seek medical care within 24 hours"
        ],
        "warnings": [
            "Popping blisters increases infection risk significantly",
            "Intact blisters are natural protection",
            "Large blisters (>2 inches) require immediate medical evaluation"
        ],
        "dos": [
            "Keep blisters intact",
            "Use sterile, non-stick dressings",
            "Watch for signs of infection (redness, pus, increased pain)",
            "Seek medical help if blisters are large or multiple"
        ],
        "donts": [
            "NEVER pop blisters",
            "Do not remove loose skin",
            "Do not apply creams that can trap heat",
            "Do not use adhesive bandages directly on blisters"
        ],
        "estimated_healing_time": "2-3 weeks with proper care",
        "supplies_needed": [
            "Sterile non-stick dressing",
            "Medical tape",
            "Antibiotic ointment (if prescribed by doctor)",
            "Pain reliever"
        ]
    },
    {
        "wound_type": "burn",
        "severity": "moderate",
        "sub_type": "skintear",
        "title": "First Aid for Burns with Skin Tears",
        "description": "Critical care for burns with open wounds or torn skin - SEEK IMMEDIATE MEDICAL CARE",
        "steps": [
            "Call emergency services or go to ER immediately",
            "Cool gently with clean water (not ice)",
            "Cover with sterile, moist dressing",
            "Do NOT remove clothing stuck to burn",
            "Keep person warm and monitor for shock"
        ],
        "warnings": [
            "HIGH RISK of infection",
            "May require skin grafting",
            "Immediate medical attention REQUIRED",
            "Watch for shock symptoms (pale skin, rapid pulse, confusion)"
        ],
        "dos": [
            "Seek emergency medical care immediately",
            "Use only sterile supplies",
            "Keep wound moist with prescribed treatment",
            "Monitor vital signs",
            "Follow medical instructions precisely"
        ],
        "donts": [
            "Do NOT attempt to clean deep wounds yourself",
            "Do NOT apply ointments without medical guidance",
            "Do NOT delay medical care for ANY reason",
            "Do NOT give food or drink if surgery may be needed"
        ],
        "estimated_healing_time": "3-6 weeks minimum (requires medical supervision)",
        "supplies_needed": [
            "Sterile gauze",
            "Saline solution",
            "Prescribed antibiotic",
            "Professional medical care",
            "Possible hospitalization"
        ]
    },

    # ============ ABRASION GUIDES ============
    {
        "wound_type": "abrasion",
        "severity": "mild",
        "sub_type": None,
        "title": "First Aid for Minor Abrasions",
        "description": "Treatment for surface abrasions",
        "steps": [
            "Rinse with clean water",
            "Gently clean with mild soap",
            "Apply antibiotic ointment",
            "Cover with bandage if needed"
        ],
        "warnings": [
            "Embedded dirt may cause infection",
            "Check for debris in wound"
        ],
        "dos": [
            "Keep moist with ointment",
            "Change bandage daily"
        ],
        "donts": [
            "Do not scrub vigorously"
        ],
        "estimated_healing_time": "1 week",
        "supplies_needed": [
            "Bandages",
            "Antibiotic ointment",
            "Mild soap"
        ]
    },
    {
        "wound_type": "abrasion",
        "severity": "moderate",
        "sub_type": None,
        "title": "First Aid for Moderate Abrasions",
        "description": "Treatment for larger or deeper abrasions",
        "steps": [
            "Rinse thoroughly with clean water for 5-10 minutes",
            "Remove any visible debris gently",
            "Apply antibiotic ointment",
            "Cover with sterile dressing",
            "Seek medical attention if deep or large"
        ],
        "warnings": [
            "Higher risk of infection",
            "May require tetanus shot",
            "Watch for signs of infection (redness, swelling, pus)"
        ],
        "dos": [
            "Keep wound clean and moist",
            "Change dressing daily",
            "Monitor for infection",
            "Apply pressure if bleeding"
        ],
        "donts": [
            "Do not scrub hard",
            "Do not use alcohol on open wounds",
            "Do not ignore signs of infection"
        ],
        "estimated_healing_time": "1-3 weeks",
        "supplies_needed": [
            "Sterile dressings",
            "Antibiotic ointment",
            "Clean water",
            "Medical tape",
            "Possible medical evaluation"
        ]
    },

    # ============ BRUISE GUIDES ============
    {
        "wound_type": "bruise",
        "severity": "mild",
        "sub_type": None,
        "title": "First Aid for Minor Bruises",
        "description": "Treatment for simple contusions",
        "steps": [
            "Apply ice pack for 15-20 minutes",
            "Elevate if possible",
            "Rest the injured area",
            "Apply gentle compression if needed"
        ],
        "warnings": [
            "Severe bruising may indicate internal injury",
            "See doctor if pain persists"
        ],
        "dos": [
            "Use ice in first 24 hours",
            "Apply heat after 24-48 hours",
            "Gentle movement after initial rest"
        ],
        "donts": [
            "Do not massage immediately",
            "Do not apply heat initially"
        ],
        "estimated_healing_time": "1-2 weeks",
        "supplies_needed": [
            "Ice pack",
            "Elastic bandage",
            "Pain reliever"
        ]
    },
    {
        "wound_type": "bruise",
        "severity": "moderate",
        "sub_type": None,
        "title": "First Aid for Moderate Bruises",
        "description": "Treatment for larger or more painful contusions",
        "steps": [
            "Apply ice pack for 15-20 minutes every 2-3 hours",
            "Elevate the injured area",
            "Rest and avoid strenuous activity",
            "Apply compression bandage if swelling is significant"
        ],
        "warnings": [
            "May indicate deeper tissue damage",
            "Monitor for signs of compartment syndrome",
            "Seek medical care if pain worsens"
        ],
        "dos": [
            "Use RICE method (Rest, Ice, Compression, Elevation)",
            "Apply heat after 48 hours",
            "Monitor for increased swelling or pain"
        ],
        "donts": [
            "Do not ignore severe pain",
            "Do not apply heat in first 48 hours",
            "Do not massage aggressively"
        ],
        "estimated_healing_time": "2-4 weeks",
        "supplies_needed": [
            "Ice packs",
            "Compression bandage",
            "Elevation pillow",
            "Pain reliever",
            "Medical evaluation if severe"
        ]
    }
]


async def seed_roles_and_permissions(session):
    """Tạo roles và permissions"""
    logger.info("Đang kiểm tra và tạo roles & permissions...")
    
    # Tạo permissions
    permission_map = {}
    for perm_data in PERMISSIONS_DATA:
        query = select(Permission).where(Permission.permission_name == perm_data["permission_name"])
        result = await session.execute(query)
        permission = result.scalar_one_or_none()
        
        if not permission:
            logger.info(f"  Tạo permission: {perm_data['permission_name']}")
            permission = Permission(
                permission_name=perm_data["permission_name"],
                description=perm_data["description"]
            )
            session.add(permission)
            await session.commit()
            await session.refresh(permission)
        
        permission_map[perm_data["permission_name"]] = permission
    
    # Tạo roles
    roles_data = [
        {"role_name": "admin", "description": "Administrator with full system access"},
        {"role_name": "user", "description": "Regular user with limited access"}
    ]
    
    role_map = {}
    for role_data in roles_data:
        query = select(Role).where(Role.role_name == role_data["role_name"])
        result = await session.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            logger.info(f"  Tạo role: {role_data['role_name']}")
            role = Role(
                role_name=role_data["role_name"],
                description=role_data["description"],
                is_active=True
            )
            session.add(role)
            await session.commit()
            await session.refresh(role)
        
        role_map[role_data["role_name"]] = role
    
    # Gán permissions cho admin role
    admin_role = role_map.get("admin")
    if admin_role:
        for perm_name in ADMIN_PERMISSIONS:
            permission = permission_map.get(perm_name)
            if permission:
                query = select(RolePermission).where(
                    RolePermission.role_id == admin_role.role_id,
                    RolePermission.permission_id == permission.permission_id
                )
                result = await session.execute(query)
                role_perm = result.scalar_one_or_none()
                
                if not role_perm:
                    role_perm = RolePermission(
                        role_id=admin_role.role_id,
                        permission_id=permission.permission_id
                    )
                    session.add(role_perm)
        await session.commit()
    
    # Gán permissions cho user role
    user_role = role_map.get("user")
    if user_role:
        for perm_name in USER_PERMISSIONS:
            permission = permission_map.get(perm_name)
            if permission:
                query = select(RolePermission).where(
                    RolePermission.role_id == user_role.role_id,
                    RolePermission.permission_id == permission.permission_id
                )
                result = await session.execute(query)
                role_perm = result.scalar_one_or_none()
                
                if not role_perm:
                    role_perm = RolePermission(
                        role_id=user_role.role_id,
                        permission_id=permission.permission_id
                    )
                    session.add(role_perm)
        await session.commit()
    
    return role_map


async def seed_admin_user(session, role_map):
    """Tạo admin user"""
    logger.info("Đang kiểm tra và tạo admin user...")
    
    # Check if admin user exists
    query = select(User).where(User.email == "admin@skinaid.com")
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        logger.info("  Tạo admin user: admin / Admin123@")
        hashed_pwd = hash_password("Admin123@")
        user = User(
            user_name="admin",
            email="admin@skinaid.com",
            hashed_password=hashed_pwd,
            is_active=True,
            is_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"  Admin user đã được tạo với ID: {user.user_id}")
    else:
        logger.info("  Admin user đã tồn tại")
    
    # Gán admin role cho user
    admin_role = role_map.get("admin")
    if admin_role and user:
        query = select(UserRole).where(
            UserRole.user_id == user.user_id,
            UserRole.role_id == admin_role.role_id
        )
        result = await session.execute(query)
        user_role = result.scalar_one_or_none()
        
        if not user_role:
            logger.info("  Gán admin role cho user...")
            user_role = UserRole(user_id=user.user_id, role_id=admin_role.role_id)
            session.add(user_role)
            await session.commit()
    
    return user


async def seed_firstaid_guides(session, admin_user):
    """Tạo firstaid guides"""
    logger.info("Đang kiểm tra và tạo firstaid guides...")
    
    created_count = 0
    for guide_data in FIRSTAID_GUIDES_DATA:
        # Check if guide exists
        query = select(FirstAidGuide).where(
            FirstAidGuide.wound_type == guide_data["wound_type"],
            FirstAidGuide.severity == guide_data["severity"]
        )
        
        # Handle sub_type
        if guide_data.get("sub_type"):
            query = query.where(FirstAidGuide.sub_type == guide_data["sub_type"])
        else:
            query = query.where(FirstAidGuide.sub_type == None)
        
        result = await session.execute(query)
        existing = result.scalar_one_or_none()
        
        if not existing:
            guide = FirstAidGuide(
                wound_type=guide_data["wound_type"],
                severity=guide_data["severity"],
                sub_type=guide_data.get("sub_type"),
                title=guide_data["title"],
                description=guide_data.get("description"),
                steps=guide_data.get("steps"),
                warnings=guide_data.get("warnings"),
                dos=guide_data.get("dos"),
                donts=guide_data.get("donts"),
                estimated_healing_time=guide_data.get("estimated_healing_time"),
                supplies_needed=guide_data.get("supplies_needed"),
                is_active=True,
                version=1,
                created_by=admin_user.user_id if admin_user else None
            )
            session.add(guide)
            created_count += 1
    
    await session.commit()
    logger.info(f"  Đã tạo {created_count} firstaid guides mới")


async def run_seed():
    """Main seed function"""
    logger.info("=" * 50)
    logger.info("BẮT ĐẦU SEED DATA")
    logger.info("=" * 50)
    
    try:
        session_maker = get_session_maker()
        async with session_maker() as session:
            # 1. Seed roles và permissions
            role_map = await seed_roles_and_permissions(session)
            
            # 2. Seed admin user
            admin_user = await seed_admin_user(session, role_map)
            
            # 3. Seed firstaid guides
            await seed_firstaid_guides(session, admin_user)
        
        logger.info("=" * 50)
        logger.info("SEED DATA HOÀN TẤT!")
        logger.info("Admin login: admin / Admin123@")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Lỗi khi seed data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_seed())
