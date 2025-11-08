"""
Script để tạo admin user cho hệ thống
"""
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from passlib.context import CryptContext

# Cấu hình database
DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/skinaid_db"

# Cấu hình password hashing
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_admin_user():
    """Tạo admin user"""
    
    # Thông tin admin user
    admin_email = input("Nhập email cho admin (mặc định: admin@skinaid.com): ").strip() or "admin@skinaid.com"
    admin_password = input("Nhập password cho admin (mặc định: Admin@123456): ").strip() or "Admin@123456"
    admin_display_name = input("Nhập tên hiển thị (mặc định: Administrator): ").strip() or "Administrator"
    
    print(f"\n=== Tạo admin user ===")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print(f"Display Name: {admin_display_name}")
    print("=====================\n")
    
    # Tạo engine và session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session_maker = async_sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    async with async_session_maker() as session:
        try:
            # Kiểm tra email đã tồn tại chưa
            check_user_sql = text("""
                SELECT user_id, email FROM users WHERE email = :email
            """)
            result = await session.execute(check_user_sql, {"email": admin_email})
            existing_user = result.mappings().first()
            
            if existing_user:
                print(f"⚠️  User với email {admin_email} đã tồn tại!")
                update_choice = input("Bạn có muốn cập nhật user này thành admin không? (y/n): ").strip().lower()
                
                if update_choice == 'y':
                    user_id = existing_user["user_id"]
                    
                    # Cập nhật password và thông tin
                    hashed_password = hash_password(admin_password)
                    update_user_sql = text("""
                        UPDATE users
                        SET hashed_password = :hashed_password,
                            display_name = :display_name,
                            is_active = true,
                            is_verified = true,
                            updated_at = :updated_at
                        WHERE user_id = :user_id
                    """)
                    await session.execute(update_user_sql, {
                        "user_id": user_id,
                        "hashed_password": hashed_password,
                        "display_name": admin_display_name,
                        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
                    })
                    
                    print(f"✅ Đã cập nhật thông tin user {admin_email}")
                else:
                    print("❌ Hủy bỏ tạo admin user")
                    return
            else:
                # Tạo user mới
                user_id = uuid.uuid4()
                current_time = datetime.now(timezone.utc).replace(tzinfo=None)
                hashed_password = hash_password(admin_password)
                
                # Insert user
                insert_user_sql = text("""
                    INSERT INTO users (user_id, email, hashed_password, display_name, is_active, is_verified, is_deleted, created_at, updated_at)
                    VALUES (:user_id, :email, :hashed_password, :display_name, :is_active, :is_verified, :is_deleted, :created_at, :updated_at)
                """)
                await session.execute(insert_user_sql, {
                    "user_id": user_id,
                    "email": admin_email,
                    "hashed_password": hashed_password,
                    "display_name": admin_display_name,
                    "is_active": True,
                    "is_verified": True,
                    "is_deleted": False,
                    "created_at": current_time,
                    "updated_at": current_time
                })
                
                # Insert user profile
                insert_profile_sql = text("""
                    INSERT INTO user_profiles (user_id, full_name, created_at, updated_at)
                    VALUES(:user_id, :full_name, :created_at, :updated_at)
                """)
                await session.execute(insert_profile_sql, {
                    "user_id": user_id,
                    "full_name": admin_display_name,
                    "created_at": current_time,
                    "updated_at": current_time
                })
                
                print(f"✅ Đã tạo user mới {admin_email}")
            
            # Lấy role admin
            get_admin_role_sql = text("""
                SELECT role_id FROM roles WHERE role_name = 'admin' AND is_active = true
            """)
            role_result = await session.execute(get_admin_role_sql)
            admin_role = role_result.mappings().first()
            
            if not admin_role:
                print("⚠️  Không tìm thấy role 'admin', đang tạo role...")
                
                # Tạo admin role
                admin_role_id = uuid.uuid4()
                create_role_sql = text("""
                    INSERT INTO roles (role_id, role_name, description, is_active, created_at, updated_at)
                    VALUES (:role_id, :role_name, :description, :is_active, :created_at, :updated_at)
                    RETURNING role_id
                """)
                current_time = datetime.now(timezone.utc).replace(tzinfo=None)
                role_result = await session.execute(create_role_sql, {
                    "role_id": admin_role_id,
                    "role_name": "admin",
                    "description": "Administrator role with full permissions",
                    "is_active": True,
                    "created_at": current_time,
                    "updated_at": current_time
                })
                
                print(f"✅ Đã tạo role 'admin'")
            else:
                admin_role_id = admin_role["role_id"]
                print(f"✅ Đã tìm thấy role 'admin'")
            
            # Kiểm tra user đã có role admin chưa
            check_user_role_sql = text("""
                SELECT * FROM user_roles WHERE user_id = :user_id AND role_id = :role_id
            """)
            user_role_result = await session.execute(check_user_role_sql, {
                "user_id": user_id,
                "role_id": admin_role_id
            })
            existing_user_role = user_role_result.mappings().first()
            
            if not existing_user_role:
                # Gán role admin cho user
                insert_user_role_sql = text("""
                    INSERT INTO user_roles (user_id, role_id, assigned_at)
                    VALUES (:user_id, :role_id, :assigned_at)
                """)
                await session.execute(insert_user_role_sql, {
                    "user_id": user_id,
                    "role_id": admin_role_id,
                    "assigned_at": datetime.now(timezone.utc).replace(tzinfo=None)
                })
                print(f"✅ Đã gán role 'admin' cho user")
            else:
                print(f"ℹ️  User đã có role 'admin'")
            
            # Commit transaction
            await session.commit()
            
            print("\n" + "="*50)
            print("🎉 TẠO ADMIN USER THÀNH CÔNG!")
            print("="*50)
            print(f"📧 Email: {admin_email}")
            print(f"🔑 Password: {admin_password}")
            print(f"👤 Display Name: {admin_display_name}")
            print(f"🆔 User ID: {user_id}")
            print("="*50)
            print("\n✨ Bạn có thể đăng nhập với thông tin trên!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Lỗi khi tạo admin user: {str(e)}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("="*50)
    print("    SCRIPT TẠO ADMIN USER - SKINAID SYSTEM")
    print("="*50)
    print()
    
    asyncio.run(create_admin_user())
