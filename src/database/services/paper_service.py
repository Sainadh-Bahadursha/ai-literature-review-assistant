from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import Paper
from src.exceptions.custom_exceptions import (
    DuplicatePaperException,
    PaperProcessingException,
)
from src.storage.supabase_storage import (
    delete_file,
    upload_file,
)
from src.utils.file_utils import calculate_file_hash


# ---------------------------------------------------------
# Paper Queries
# ---------------------------------------------------------


def get_paper_by_hash(
    db: Session,
    file_hash: str,
) -> Paper | None:
    """
    Find a paper using its SHA-256 file hash.

    Used to check whether a paper has already
    been uploaded.
    """

    statement = select(Paper).where(
        Paper.file_hash == file_hash
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_paper_by_id(
    db: Session,
    paper_id: UUID,
) -> Paper | None:
    """
    Find a paper using its unique ID.
    """

    statement = select(Paper).where(
        Paper.id == paper_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_papers_by_user(
    db: Session,
    user_id: UUID,
) -> list[Paper]:
    """
    Get all papers belonging to a user.

    Papers are returned from newest to oldest.
    """

    statement = (
        select(Paper)
        .where(Paper.user_id == user_id)
        .order_by(Paper.created_at.desc())
    )

    return list(
        db.execute(statement).scalars().all()
    )


# ---------------------------------------------------------
# Paper Creation
# ---------------------------------------------------------


def create_paper(
    db: Session,
    user_id: UUID,
    title: str,
    file_name: str,
    file_hash: str,
    authors: str | None = None,
    abstract: str | None = None,
    publication_year: int | None = None,
    doi: str | None = None,
    storage_path: str | None = None,
) -> Paper:
    """
    Create and save a paper record.

    The actual PDF is stored in Supabase Storage.
    PostgreSQL stores the paper metadata and
    storage path.
    """

    paper = Paper(
        user_id=user_id,
        title=title,
        authors=authors,
        abstract=abstract,
        publication_year=publication_year,
        doi=doi,
        file_name=file_name,
        file_hash=file_hash,
        storage_path=storage_path,
    )

    try:
        db.add(paper)
        db.commit()
        db.refresh(paper)

    except Exception:
        db.rollback()
        raise

    return paper


# ---------------------------------------------------------
# Complete Upload Workflow
# ---------------------------------------------------------


def upload_paper(
    db: Session,
    user_id: UUID,
    file_path: str,
    title: str,
    authors: str | None = None,
    abstract: str | None = None,
    publication_year: int | None = None,
    doi: str | None = None,
    bucket_name: str = "papers",
) -> Paper:
    """
    Complete paper upload workflow.

    Steps:

        1. Validate local PDF
        2. Calculate SHA-256 hash
        3. Check for duplicate paper
        4. Generate Supabase Storage path
        5. Upload PDF to Supabase Storage
        6. Create Paper record in PostgreSQL
        7. Clean up Storage if database creation fails

    Returns:
        The newly created Paper object.
    """

    file = Path(file_path)

    # -----------------------------------------------------
    # 1. Validate file
    # -----------------------------------------------------

    if not file.exists():
        raise PaperProcessingException(
            f"Paper file not found: {file_path}"
        )

    if not file.is_file():
        raise PaperProcessingException(
            f"Paper path is not a file: {file_path}"
        )

    if file.suffix.lower() != ".pdf":
        raise PaperProcessingException(
            "Only PDF files are currently supported."
        )

    # -----------------------------------------------------
    # 2. Calculate SHA-256
    # -----------------------------------------------------

    try:
        file_hash = calculate_file_hash(
            file_path=file_path,
        )

    except Exception as exc:
        raise PaperProcessingException(
            f"Unable to calculate file hash: {exc}"
        ) from exc

    print("File hash:", file_hash)

    # -----------------------------------------------------
    # 3. Check for duplicate
    # -----------------------------------------------------

    existing_paper = get_paper_by_hash(
        db=db,
        file_hash=file_hash,
    )

    if existing_paper:
        raise DuplicatePaperException(
            "This paper has already been uploaded. "
            f"Existing paper ID: {existing_paper.id}"
        )

    # -----------------------------------------------------
    # 4. Generate Storage path
    # -----------------------------------------------------

    storage_path = (
        f"{user_id}/{file_hash}.pdf"
    )

    print("Storage path:", storage_path)

    # -----------------------------------------------------
    # 5. Upload to Supabase Storage
    # -----------------------------------------------------

    try:

        upload_file(
            bucket_name=bucket_name,
            file_path=file_path,
            storage_path=storage_path,
        )

    except Exception as exc:
        raise PaperProcessingException(
            f"Failed to upload paper to Supabase Storage: {exc}"
        ) from exc

    # -----------------------------------------------------
    # 6. Create PostgreSQL record
    # -----------------------------------------------------

    try:

        paper = create_paper(
            db=db,
            user_id=user_id,
            title=title,
            authors=authors,
            abstract=abstract,
            publication_year=publication_year,
            doi=doi,
            file_name=file.name,
            file_hash=file_hash,
            storage_path=storage_path,
        )

    except IntegrityError as exc:

        # Database rejected the record.
        # Remove the file from Storage so that
        # we don't leave an orphaned file.

        try:
            delete_file(
                bucket_name=bucket_name,
                storage_path=storage_path,
            )
        except Exception:
            pass

        raise PaperProcessingException(
            "Paper could not be saved to the database."
        ) from exc

    except Exception as exc:

        try:
            delete_file(
                bucket_name=bucket_name,
                storage_path=storage_path,
            )
        except Exception:
            pass

        raise PaperProcessingException(
            f"Failed to create paper record: {exc}"
        ) from exc

    # -----------------------------------------------------
    # 7. Return created paper
    # -----------------------------------------------------

    return paper


# ---------------------------------------------------------
# Delete Paper
# ---------------------------------------------------------


def delete_paper(
    db: Session,
    paper: Paper,
    bucket_name: str = "papers",
) -> None:
    """
    Delete a paper from both:

        1. Supabase Storage
        2. PostgreSQL

    Related paper chunks and paper elements are
    automatically deleted because of the cascade
    configuration.
    """

    # Delete Storage file first if it exists.

    if paper.storage_path:

        try:
            delete_file(
                bucket_name=bucket_name,
                storage_path=paper.storage_path,
            )

        except Exception as exc:
            raise PaperProcessingException(
                f"Failed to delete paper from Storage: {exc}"
            ) from exc

    # Delete database record.

    try:
        db.delete(paper)
        db.commit()

    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------
# Manual Smoke Test
# ---------------------------------------------------------


if __name__ == "__main__":

    from uuid import uuid4

    from src.database.connection import SessionLocal
    from src.database.services.profile_service import (
        create_profile,
    )

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # 1. Create test profile
        # -------------------------------------------------

        test_user_id = uuid4()

        profile = create_profile(
            db=db,
            user_id=test_user_id,
            full_name="Paper Upload Test User",
        )

        print("\nProfile created successfully!")
        print("User ID:", profile.id)

        # -------------------------------------------------
        # 2. Upload actual PDF
        # -------------------------------------------------

        paper = upload_paper(
            db=db,
            user_id=profile.id,
            file_path="data/test_pdfs/sample.pdf",
            title="Test Research Paper",
            authors="Test Author",
            abstract="Test abstract",
            publication_year=2026,
        )

        print("\nPaper uploaded successfully!")

        print("Paper ID:")
        print(paper.id)

        print("\nTitle:")
        print(paper.title)

        print("\nFile name:")
        print(paper.file_name)

        print("\nFile hash:")
        print(paper.file_hash)

        print("\nStorage path:")
        print(paper.storage_path)

        # -------------------------------------------------
        # 3. Retrieve paper
        # -------------------------------------------------

        found_paper = get_paper_by_id(
            db=db,
            paper_id=paper.id,
        )

        print("\nPaper lookup:")

        if found_paper:
            print("Paper found successfully!")
            print("Title:", found_paper.title)
        else:
            print("Paper not found.")

        # -------------------------------------------------
        # 4. Get user's papers
        # -------------------------------------------------

        user_papers = get_papers_by_user(
            db=db,
            user_id=profile.id,
        )

        print("\nPapers belonging to user:")

        for item in user_papers:
            print(
                f"- {item.title} | "
                f"{item.file_name}"
            )

    finally:

        db.close()