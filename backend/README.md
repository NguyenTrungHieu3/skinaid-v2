# SkinAid Backend API

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

Một dịch vụ backend dựa trên FastAPI cho ứng dụng phát hiện tình trạng da SkinAid - một giải pháp toàn diện để phân tích vết thương và cung cấp hướng dẫn sơ cứu.

## 📋 Mục lục

- [Tổng quan](#tổng-quan)
- [Tính năng chính](#tính-năng-chính)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [API Endpoints](#api-endpoints)
- [Cấu trúc cơ sở dữ liệu](#cấu-trúc-cơ-sở-dữ-liệu)
- [Cấu hình môi trường](#cấu-hình-môi-trường)
- [Testing](#testing)
- [Contributing](#contributing)

## 🎯 Tổng quan

SkinAid Backend API là một hệ thống phân tích vết thương thông minh sử dụng trí tuệ nhân tạo để:

- **Phân tích hình ảnh vết thương** với độ chính xác cao
- **Phân loại mức độ nghiêm trọng** của vết thương
- **Hỗ trợ phân loại phụ đặc biệt** cho vết bỏng (blister, skintear)
- **Cung cấp hướng dẫn sơ cứu** phù hợp với từng loại vết thương
- **Quản lý người dùng** với hệ thống xác thực JWT an toàn

## ✨ Tính năng chính

### 🔐 Xác thực và phân quyền
- **JWT Authentication**: Xác thực người dùng với access token và refresh token
- **Email Verification**: Xác thực email với mã token
- **Password Management**: Đặt lại mật khẩu, thay đổi mật khẩu
- **User Profiles**: Quản lý thông tin cá nhân chi tiết

### 🤖 AI-Powered Analysis
- **Wound Detection**: Phát hiện và phân loại vết thương từ hình ảnh
- **Severity Classification**: Xác định mức độ nghiêm trọng (mild, moderate, severe)
- **Burn Sub-types**: Hỗ trợ đặc biệt cho vết bỏng có blister và skintear
- **Analysis History**: Lưu trữ và truy xuất lịch sử phân tích

### 🏥 First Aid Knowledge Base
- **Comprehensive Guides**: Hướng dẫn sơ cứu toàn diện cho mọi loại vết thương
- **Smart Matching**: Tự động tìm hướng dẫn phù hợp dựa trên phân tích AI
- **Multi-language Support**: Hỗ trợ đa ngôn ngữ (sẵn sàng mở rộng)

### 📊 Upload Management
- **File Upload Tracking**: Theo dõi lịch sử upload hình ảnh
- **Statistics**: Thống kê hoạt động upload
- **Storage Management**: Quản lý bộ nhớ hiệu quả

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   PostgreSQL    │
│   (React)       │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Service    │
                       │   (PyTorch)     │
                       └─────────────────┘
```

### Công nghệ sử dụng

- **Framework**: FastAPI (0.116.1)
- **Database**: PostgreSQL với asyncpg
- **ORM**: SQLModel (0.0.24)
- **Authentication**: JWT với python-jose
- **AI/ML**: PyTorch, torchvision, timm, ultralytics
- **Image Processing**: OpenCV, Pillow
- **Email Service**: SMTP với python-email-validator
- **Testing**: pytest với pytest-asyncio

## 🚀 Cài đặt và chạy

### Yêu cầu hệ thống

- **Python**: 3.8 trở lên
- **PostgreSQL**: 15 trở lên
- **pip**: Package manager cho Python

### Hướng dẫn cài đặt

1. **Điều hướng đến thư mục backend**
   ```bash
   cd backend
   ```

2. **Tạo môi trường ảo**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Cài đặt dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Cấu hình biến môi trường**
   ```bash
   cp .env.example .env
   # Chỉnh sửa file .env với thông tin cấu hình của bạn
   ```

5. **Khởi tạo cơ sở dữ liệu**
   ```bash
   # Đảm bảo PostgreSQL đang chạy
   # Cập nhật DATABASE_URL trong .env nếu cần
   ```

6. **Chạy ứng dụng**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Truy cập tài liệu API**
   - **Swagger UI**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc
   - **API Root**: http://localhost:8000/

## 📁 Cấu trúc dự án

```
backend/
├── app/                          # Ứng dụng chính
│   ├── main.py                   # Entry point của ứng dụng
│   ├── __init__.py
│   ├── api/                      # API versioning
│   │   └── v1/
│   │       ├── api.py            # Router tổng hợp
│   │       └── deps.py           # Dependencies
│   ├── core/                     # Core configuration
│   │   ├── config.py             # Cấu hình ứng dụng
│   │   ├── database.py           # Cấu hình cơ sở dữ liệu
│   │   └── middleware/           # Middleware tùy chỉnh
│   ├── modules/                  # Các module chức năng
│   │   ├── auth/                 # Xác thực và phân quyền
│   │   │   ├── controllers/      # Business logic
│   │   │   ├── models/           # Database models
│   │   │   ├── routes/           # API routes
│   │   │   ├── schemas/          # Pydantic schemas
│   │   │   └── services/         # Service layer
│   │   ├── ai/                   # AI xử lý
│   │   │   ├── controllers/
│   │   │   ├── models/
│   │   │   ├── routes/
│   │   │   ├── schemas/
│   │   │   └── services/
│   │   ├── profile/              # Quản lý profile
│   │   ├── upload/               # Upload logs
│   │   └── firstaid/             # Hướng dẫn sơ cứu
│   ├── shared/                   # Shared components
│   │   ├── models/               # Base models
│   │   ├── schemas/              # Shared schemas
│   │   └── enum.py               # Enums
│   └── utils/                    # Utilities
│       ├── constants/            # Hằng số
│       ├── exceptions/           # Custom exceptions
│       ├── helpers/              # Helper functions
│       ├── validators/           # Validation logic
│       └── email_service.py      # Email service
├── tests/                        # Test files
├── uploads/                      # Uploaded files
├── docs/                         # Documentation
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── pytest.ini                   # Pytest configuration
└── README.md                     # Tài liệu dự án
```

## 🔗 API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/signup` | Đăng ký tài khoản mới |
| POST | `/signin` | Đăng nhập hệ thống |
| POST | `/verify-email` | Xác thực email (POST) |
| GET | `/verify-email` | Xác thực email qua link |
| GET | `/me` | Thông tin user hiện tại |
| POST | `/password-reset/request` | Yêu cầu đặt lại mật khẩu |
| POST | `/password-reset/confirm` | Xác nhận đặt lại mật khẩu |
| POST | `/refresh` | Làm mới access token |
| POST | `/logout` | Đăng xuất |
| POST | `/resend-verification` | Gửi lại email xác thực |
| POST | `/change-password` | Thay đổi mật khẩu |
| GET | `/health` | Kiểm tra trạng thái service |

### User Profile (`/api/v1/profile`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| PUT | `/update` | Cập nhật thông tin profile |
| GET | `/me` | Lấy thông tin profile hiện tại |
| GET | `/statistics` | Lấy thống kê profile |
| GET | `/search` | Tìm kiếm profiles |
| GET | `/completion-suggestions` | Gợi ý hoàn thiện profile |

### AI Analysis (`/api/v1/ai`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health` | Kiểm tra trạng thái AI models |
| POST | `/analyze` | Phân tích hình ảnh vết thương |
| GET | `/history` | Lịch sử phân tích của user |

### First Aid (`/api/v1/first-aid`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/guide/{wound_type}/{severity}` | Lấy hướng dẫn sơ cứu |
| GET | `/wound-types` | Danh sách loại vết thương |
| GET | `/search` | Tìm kiếm hướng dẫn sơ cứu |
| GET | `/statistics` | Thống kê first aid |
| GET | `/validate/{wound_type}/{severity}` | Kiểm tra tính khả dụng |

### Upload (`/api/v1/upload`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/logs` | Lịch sử upload logs |
| GET | `/statistics` | Thống kê upload |

## 🗄️ Cấu trúc cơ sở dữ liệu

### Các bảng chính

#### Authentication & Users
- **users**: Thông tin xác thực người dùng
- **user_profiles**: Thông tin cá nhân mở rộng
- **verification_tokens**: Token xác thực email
- **roles**: Vai trò người dùng
- **permissions**: Quyền hạn hệ thống
- **user_roles**: Liên kết user-role
- **role_permissions**: Liên kết role-permission

#### AI Analysis
- **wound_analyses**: Kết quả phân tích vết thương
- **wound_detections**: Thông tin phát hiện vết thương

#### First Aid
- **firstaid_guides**: Hướng dẫn sơ cứu

#### Upload Management
- **upload_logs**: Lịch sử upload hình ảnh

## ⚙️ Cấu hình môi trường

### Các biến môi trường quan trọng

```bash
# Ứng dụng
APP_NAME="Wound Detection API"
DEBUG=true
API_V1_STR="/api/v1"

# Cơ sở dữ liệu
DATABASE_URL="postgresql+asyncpg://postgres:123456@localhost:5432/skinaid_db"

# JWT Authentication
SECRET_KEY="your-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Service
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-app-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# File Upload
UPLOAD_MAX_FILE_SIZE=5242880  # 5MB
UPLOAD_ALLOWED_FORMATS=".jpg,.jpeg,.png"
UPLOAD_MIN_WIDTH=224
UPLOAD_MIN_HEIGHT=224

# AI Service
AI_SERVICE_URL="http://localhost:8001"
AI_SERVICE_TIMEOUT=30
```

### Các chế độ môi trường

- **Development**: `DEBUG=true, TESTING=false`
- **Testing**: `DEBUG=false, TESTING=true`
- **Production**: `DEBUG=false, TESTING=false`

## 🧪 Testing

Chạy test suite:

```bash
# Chạy tất cả tests
pytest tests/ -v

# Chạy với coverage
pytest tests/ --cov=app --cov-report=html

# Chạy tests theo module
pytest tests/test_auth.py -v
pytest tests/test_ai.py -v
```

## 🔥 Tính năng đặc biệt: Burn Sub-types

Hệ thống hỗ trợ xử lý đặc biệt cho vết bỏng với các loại phụ:

### Các loại phụ được hỗ trợ
- **Blister** (`blister`): Vết bỏng có mụn nước
- **Skin Tear** (`skintear`): Vết bỏng kèm rách da

### Cách hoạt động
1. **AI Detection**: Model AI phát hiện mức độ `moderate_blister` hoặc `moderate_skintear`
2. **Smart Parsing**: Hệ thống tự động trích xuất loại phụ từ kết quả
3. **Guide Matching**: Tìm hướng dẫn chuyên biệt trước, fallback về hướng dẫn chung
4. **Response**: Trả về hướng dẫn phù hợp với loại phụ

## 🤝 Contributing

1. Tuân thủ cấu trúc code hiện tại
2. Viết tests cho tính năng mới
3. Cập nhật tài liệu khi thay đổi API
4. Sử dụng type hints trong toàn bộ code
5. Tuân thủ Python PEP 8 style guidelines
6. Tạo Pull Request với mô tả chi tiết

## 📚 Tài liệu bổ sung

- [Environment Configuration Guide](ENVIRONMENT_MODES_GUIDE.md)
- [Quick Reference](ENVIRONMENT_QUICK_REFERENCE.md)
- [Backend Architecture Guide](BACKEND_GUIDE.md)
- [RBAC Implementation Guide](docs/RBAC_IMPLEMENTATION_GUIDE.md)

## 📄 License

Dự án này là một phần của SkinAid Capstone project.

---

**Nhóm phát triển**: SkinAid Team
**Version**: 0.1.0
**Last Updated**: 2025-01-22