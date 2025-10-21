# SkinAid Backend API

A FastAPI-based backend service for the SkinAid skin condition detection application.

## Features

- **User Authentication**: JWT-based authentication with email verification
- **User Profiles**: Complete user profile management
- **AI-Powered Wound Analysis**: Advanced wound detection and classification
- **Burn Sub-types Support**: Specialized handling for burn blisters and skin tears
- **First Aid Knowledge Base**: Comprehensive first aid guides with severity levels
- **Database Integration**: PostgreSQL with SQLModel ORM
- **Testing**: Comprehensive test suite with pytest
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- pip package manager

### Installation

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
   
   📖 **See [Environment Configuration Guide](ENVIRONMENT_MODES_GUIDE.md) for detailed explanations of all modes and settings.**
   
   🚀 **See [Quick Reference](ENVIRONMENT_QUICK_REFERENCE.md) for common setup scenarios.**

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Burn Sub-types Support

The system now supports specialized handling for burn wounds with sub-types:

### Supported Burn Sub-types
- **Blister** (`blister`): Burns with blisters - requires careful handling
- **Skin Tear** (`skintear`): Burns with skin tears - needs immediate attention

### How It Works
1. **AI Detection**: AI model detects burn severity as `moderate_blister` or `moderate_skintear`
2. **Smart Parsing**: System automatically extracts sub-type from severity string
3. **Guide Matching**: Searches for specialized first aid guide first, falls back to general burn guide
4. **Response**: Returns appropriate first aid instructions based on sub-type

### Example AI Classifications
- `burn_moderate_blister` → Searches for blister-specific guide
- `burn_moderate_skintear` → Searches for skintear-specific guide
- `burn_severe` → Uses general severe burn guide

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/verify-email` - Verify email address
- `GET /api/v1/auth/me` - Get current user info

### User Profile
- `GET /api/v1/profile/me` - Get current user profile
- `PUT /api/v1/profile/me` - Update user profile

### AI Analysis
- `POST /api/v1/ai/analyze` - Analyze wound image with AI (supports burn sub-types)
- `GET /api/v1/ai/health` - Check AI service health
- `GET /api/v1/ai/history` - Get user's analysis history

### First Aid
- `GET /api/v1/firstaid/guides` - Get first aid guides
- `GET /api/v1/firstaid/wound-types` - Get available wound types

## Database Schema

The application uses the following main models:

- **User**: Core user authentication data
- **UserProfile**: Extended user profile information
- **VerificationToken**: Email verification tokens

## Environment Variables

## Environment Variables

The application supports multiple environment modes:

- **Development Mode** (`DEBUG=true`, `TESTING=false`): Full debugging with real services
- **Testing Mode** (`DEBUG=false`, `TESTING=true`): Mock services for automated testing  
- **Production Mode** (`DEBUG=false`, `TESTING=false`): Optimized for live deployment

📖 **Complete documentation:** [Environment Modes Guide](ENVIRONMENT_MODES_GUIDE.md)

🚀 **Quick setup:** [Environment Quick Reference](ENVIRONMENT_QUICK_REFERENCE.md)

## Project Structure

See `BACKEND_GUIDE.md` for detailed project structure and architecture information.

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation for API changes
4. Use type hints throughout the code
5. Follow Python PEP 8 style guidelines

## License

This project is part of the SkinAid Capstone project.