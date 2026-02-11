import os


def check_encoding(start_path):
    for root, dirs, files in os.walk(start_path):
        if "venv" in dirs:
            dirs.remove("venv")
        if ".git" in dirs:
            dirs.remove(".git")
        if ".pytest_cache" in dirs:
            dirs.remove(".pytest_cache")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")

        for file in files:
            # if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, 'rb') as f:
                    raw = f.read(4)  # Read first 4 bytes

                if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
                    print(f"BOM detected: {path}")

                # Try deciding as utf-8 (needs full read, maybe slow for large files)
                # Optimization: Just check start byte for 0xff
                if raw and raw[0] == 0xff:
                    print(f"Starts with 0xff: {path}")

            except Exception as e:
                # print(f"Error reading {path}: {e}")
                pass


if __name__ == "__main__":
    check_encoding(".")
