import importlib.metadata
import re

REQUIREMENTS_FILE = "requirements.txt"

with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()

        # Ignore blank lines and comments
        if not line or line.startswith("#"):
            continue

        # Ignore requirement options such as -r, --index-url, etc.
        if line.startswith("-"):
            continue

        # Remove environment markers
        line = line.split(";")[0].strip()

        # Extract package name
        match = re.match(r"^([A-Za-z0-9_.-]+)", line)

        if not match:
            continue

        package = match.group(1)

        try:
            version = importlib.metadata.version(package)
            print(f"{package}=={version}")

        except importlib.metadata.PackageNotFoundError:
            print(f"# {package} - NOT INSTALLED")