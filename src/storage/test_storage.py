from src.storage.supabase_storage import upload_file


if __name__ == "__main__":

    local_file = "data/test_pdfs/NIPS-2017-attention-is-all-you-need-Paper.pdf"

    storage_path = upload_file(
        bucket_name="papers",
        file_path=local_file,
        storage_path="test/sample.pdf",
    )

    print("Upload successful!")
    print("Storage path:", storage_path)