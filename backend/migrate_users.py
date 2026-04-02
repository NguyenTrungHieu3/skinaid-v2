import os
import shutil
from pathlib import Path

backend_dir = Path("d:/NCKH_REFACTOR/skinaid-v2/backend")
users_dir = backend_dir / "app" / "modules" / "users"

dirs_to_delete = [
    users_dir / "models",
    users_dir / "routes",
    users_dir / "repository",
    users_dir / "schemas",
    users_dir / "services",
    users_dir / "utils",
]

files_to_delete = [
    users_dir / "dependencies.py",
    users_dir / "device_sessions.py",
]

for d in dirs_to_delete:
    if d.exists():
        shutil.rmtree(d)

for f in files_to_delete:
    if f.exists():
        f.unlink()

replacements = {
    "app.modules.users.models": "app.modules.users.models",
    "app.modules.users.schemas": "app.modules.users.schemas",
    "app.modules.users.service": "app.modules.users.service",
    "app.modules.users.repository": "app.modules.users.repository",
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

print("Users directory refactored successfully.")
