import hashlib
from pathlib import Path


def calculate_file_hash(
    file_path: str,
    algorithm: str = "sha256",
) -> str:
    """
    Calculate the hash of a file.

    Returns:
        Hexadecimal hash string.
    """

    file = Path(file_path)

    if not file.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    hash_function = hashlib.new(algorithm)

    with open(file, "rb") as f:
        while chunk := f.read(8192):
            hash_function.update(chunk)

    return hash_function.hexdigest()

if __name__ == "__main__":

    file_path = "data/test_pdfs/sample.pdf"

    file_hash = calculate_file_hash(file_path)

    print("File:", file_path)
    print("SHA-256:", file_hash)
    print("Hash length:", len(file_hash))