from pathlib import Path

from supabase import create_client, Client

from src.config.settings import settings


# ============================================================
# Supabase Client
# ============================================================

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_secret_key,
)


# ============================================================
# Upload File
# ============================================================

def upload_file(
    bucket_name: str,
    file_path: str,
    storage_path: str,
) -> str:
    """
    Upload a local file to Supabase Storage.

    Returns the storage path of the uploaded file.
    """

    file = Path(file_path)

    if not file.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(file, "rb") as f:
        supabase.storage.from_(bucket_name).upload(
            path=storage_path,
            file=f,
            file_options={
                "content-type": "application/pdf",
                "upsert": False,
            },
        )

    return storage_path


# ============================================================
# Delete File
# ============================================================

def delete_file(
    bucket_name: str,
    storage_path: str,
) -> None:
    """
    Delete a file from Supabase Storage.
    """

    supabase.storage.from_(bucket_name).remove(
        [storage_path]
    )


# ============================================================
# Get Public URL
# ============================================================

def get_public_url(
    bucket_name: str,
    storage_path: str,
) -> str:
    """
    Return the public URL of a stored file.

    This should only be used for public buckets.
    """

    return supabase.storage.from_(bucket_name).get_public_url(
        storage_path
    )

if __name__ == "__main__":

    local_file = "data/test_pdfs/sample.pdf"

    storage_path = upload_file(
        bucket_name="papers",
        file_path=local_file,
        storage_path="test/sample_1.pdf",
    )

    print("Upload successful!")
    print("Storage path:", storage_path)