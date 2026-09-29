from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import PaperElement
from src.document_parser.parser import extract_document_content
from src.storage.supabase_storage import upload_figure


def create_paper_element(
    db: Session,
    paper_id: UUID,
    element_type: str,
    element_number: int,
    page_number: int | None = None,
    content: dict | None = None,
    storage_path: str | None = None,
    description: str | None = None,
) -> PaperElement:
    """
    Create a figure or table element for a paper.
    """

    element = PaperElement(
        paper_id=paper_id,
        type=element_type,
        element_number=element_number,
        page_number=page_number,
        content=content,
        storage_path=storage_path,
        description=description,
    )

    try:
        db.add(element)
        db.commit()
        db.refresh(element)

    except Exception:
        db.rollback()
        raise

    return element


def get_elements_by_paper(
    db: Session,
    paper_id: UUID,
) -> list[PaperElement]:
    """
    Get all elements belonging to a paper.
    """

    statement = (
        select(PaperElement)
        .where(PaperElement.paper_id == paper_id)
        .order_by(
            PaperElement.type,
            PaperElement.element_number,
        )
    )

    return list(
        db.execute(statement)
        .scalars()
        .all()
    )


def get_figures_by_paper(
    db: Session,
    paper_id: UUID,
) -> list[PaperElement]:
    """
    Get all figures belonging to a paper.
    """

    statement = (
        select(PaperElement)
        .where(
            PaperElement.paper_id == paper_id,
            PaperElement.type == "figure",
        )
        .order_by(PaperElement.element_number)
    )

    return list(
        db.execute(statement)
        .scalars()
        .all()
    )


def get_tables_by_paper(
    db: Session,
    paper_id: UUID,
) -> list[PaperElement]:
    """
    Get all tables belonging to a paper.
    """

    statement = (
        select(PaperElement)
        .where(
            PaperElement.paper_id == paper_id,
            PaperElement.type == "table",
        )
        .order_by(PaperElement.element_number)
    )

    return list(
        db.execute(statement)
        .scalars()
        .all()
    )


def delete_paper_element(
    db: Session,
    element: PaperElement,
) -> None:
    """
    Delete a paper element from the database.
    """

    try:
        db.delete(element)
        db.commit()

    except Exception:
        db.rollback()
        raise


def save_document_elements(
    db: Session,
    paper_id: UUID,
    document,
    user_id: UUID,
    file_hash: str,
    bucket_name: str = "papers",
) -> list[PaperElement]:
    """
    Save figures and tables extracted from a Docling document.

    Figures:
        - Keep image in memory
        - Upload image directly to Supabase Storage
        - Save figure metadata in PostgreSQL

    Tables:
        - Save structured table data in PostgreSQL
    """

    extracted_content = extract_document_content(
        document
    )

    saved_elements = []

    # --------------------------------------------------
    # Save figures
    # --------------------------------------------------

    for figure in extracted_content["figures"]:

        image = figure["image"]

        # Skip figures that Docling could not extract
        if image is None:
            print(
                f"Skipping Figure "
                f"{figure['figure_number']} "
                f"because image extraction failed."
            )
            continue

        storage_path = (
            f"{user_id}/"
            f"{file_hash}/"
            f"figure-{figure['figure_number']}.png"
        )

        print(
            f"Uploading Figure "
            f"{figure['figure_number']}..."
        )

        upload_figure(
            image=image,
            storage_path=storage_path,
            bucket_name=bucket_name,
        )

        print(
            f"Figure "
            f"{figure['figure_number']} "
            f"uploaded successfully."
        )

        element = create_paper_element(
            db=db,
            paper_id=paper_id,
            element_type="figure",
            element_number=figure["figure_number"],
            page_number=figure["page_number"],
            storage_path=storage_path,
            description=figure["caption"] or None,
        )

        saved_elements.append(element)

    # --------------------------------------------------
    # Save tables
    # --------------------------------------------------

    for table in extracted_content["tables"]:

        content = {
            "headers": table["headers"],
            "rows": table["rows"],
            "markdown": table["markdown"],
        }

        element = create_paper_element(
            db=db,
            paper_id=paper_id,
            element_type="table",
            element_number=table["table_number"],
            page_number=table["page_number"],
            content=content,
            description=table["caption"] or None,
        )

        saved_elements.append(element)

        print(
            f"Table "
            f"{table['table_number']} "
            f"saved successfully."
        )

    return saved_elements

if __name__ == "__main__":
    from uuid import uuid4

    from src.database.connection import SessionLocal
    from src.database.services.paper_service import (
        create_paper,
        get_paper_by_hash,
    )
    from src.database.services.profile_service import create_profile
    from src.document_parser.parser import parse_document
    from src.utils.file_utils import calculate_file_hash

    db = SessionLocal()

    try:
        # --------------------------------------------------
        # 1. Test PDF
        # --------------------------------------------------

        file_path = "data/test_pdfs/sample.pdf"

        file_hash = calculate_file_hash(
            file_path
        )

        print("File hash:")
        print(file_hash)

        # --------------------------------------------------
        # 2. Check whether this paper already exists
        # --------------------------------------------------

        paper = get_paper_by_hash(
            db=db,
            file_hash=file_hash,
        )

        if paper:

            print("\nExisting paper found:")
            print("Paper ID:", paper.id)
            print("Title:", paper.title)
            print("User ID:", paper.user_id)

        else:

            # --------------------------------------------------
            # 3. Create test profile
            # --------------------------------------------------

            user_id = uuid4()

            profile = create_profile(
                db=db,
                user_id=user_id,
                full_name="Document Element Test User",
            )

            print("\nProfile created:")
            print(profile.id)

            # --------------------------------------------------
            # 4. Create paper
            # --------------------------------------------------

            paper = create_paper(
                db=db,
                user_id=profile.id,
                title="Attention Is All You Need",
                file_name="sample.pdf",
                file_hash=file_hash,
            )

            print("\nPaper created:")
            print(paper.id)

        # --------------------------------------------------
        # 5. Parse PDF using Docling
        # --------------------------------------------------

        print("\nParsing PDF with Docling...")

        document = parse_document(
            file_path
        )

        print(
            "Document parsed successfully."
        )

        # --------------------------------------------------
        # 6. Save figures and tables
        # --------------------------------------------------

        print(
            "\nSaving figures and tables..."
        )

        elements = save_document_elements(
            db=db,
            paper_id=paper.id,
            document=document,
            user_id=paper.user_id,
            file_hash=file_hash,
        )

        # --------------------------------------------------
        # 7. Display results
        # --------------------------------------------------

        print(
            f"\nSaved {len(elements)} elements."
        )

        for element in elements:

            print(
                f"- {element.type} "
                f"{element.element_number} "
                f"| page {element.page_number}"
            )

            if element.storage_path:
                print(
                    f"  Storage: "
                    f"{element.storage_path}"
                )

    finally:
        db.close()