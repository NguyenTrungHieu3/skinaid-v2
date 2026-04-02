import os
import shutil
from pathlib import Path

backend_dir = Path("d:/NCKH_REFACTOR/skinaid-v2/backend")
users_dir = backend_dir / "app" / "modules" / "users"
profile_dir = backend_dir / "app" / "modules" / "profile"

profile_dir.mkdir(parents=True, exist_ok=True)
(profile_dir / "__init__.py").touch()

files_to_move = [
    (users_dir / "models" / "user_profile.py", profile_dir / "models.py", True),
    (users_dir / "models" / "device_sessions.py", None, False), # we will append to models.py
]

# We will read user_profile and device_sessions and put them into profile/models.py
user_profile_content = ""
device_sessions_content = ""
if (users_dir / "models" / "user_profile.py").exists():
    with open(users_dir / "models" / "user_profile.py", "r", encoding="utf-8") as f:
        user_profile_content = f.read()
if (users_dir / "models" / "device_sessions.py").exists():
    with open(users_dir / "models" / "device_sessions.py", "r", encoding="utf-8") as f:
        device_sessions_content = f.read()

# Merge models, remove duplicate imports if any (basic merge)
with open(profile_dir / "models.py", "w", encoding="utf-8") as f:
    f.write(user_profile_content + "\n\n" + device_sessions_content)

# Move others
shutil.copy(users_dir / "routes" / "profile_router.py", profile_dir / "router.py")
shutil.copy(users_dir / "services" / "profile_service.py", profile_dir / "service.py")
shutil.copy(users_dir / "repository" / "profile_repository.py", profile_dir / "repository.py")
shutil.copy(users_dir / "schemas" / "profile_schemas.py", profile_dir / "schemas.py")

replacements = {
    "app.modules.profile.models": "app.modules.profile.models",
    "app.modules.profile.models": "app.modules.profile.models",
    "app.modules.profile.router": "app.modules.profile.router",
    "app.modules.profile.service": "app.modules.profile.service",
    "app.modules.profile.repository": "app.modules.profile.repository",
    "app.modules.profile.schemas": "app.modules.profile.schemas",
}

for root, dirs, files in os.walk(backend_dir):
    dirs[:] = [d for d in dirs if d not in {".git", "venv", "env", "__pycache__", ".venv", "tests"}]
    for str_file in files:
        if str_file.endswith(".py"):
            file_path = Path(root) / str_file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = content
            for old_import, new_import in replacements.items():
                new_content = new_content.replace(old_import, new_import)
            
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

print("Migration completed successfully.")
