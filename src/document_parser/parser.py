from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)

from src.exceptions.custom_exceptions import (
    PaperProcessingException,
)


# ---------------------------------------------------------
# Document Parsing
# ---------------------------------------------------------


def parse_document(
    file_path: str,
):
    """
    Parse a PDF document using Docling.

    Picture images are explicitly enabled so that
    figures can later be extracted and stored in
    Supabase Storage.

    Args:
        file_path: Path to the PDF file.

    Returns:
        DoclingDocument.
    """

    file = Path(file_path)

    if not file.exists():
        raise PaperProcessingException(
            f"Document not found: {file_path}"
        )

    if not file.is_file():
        raise PaperProcessingException(
            f"Document path is not a file: {file_path}"
        )

    if file.suffix.lower() != ".pdf":
        raise PaperProcessingException(
            "Only PDF files are currently supported."
        )

    try:
        # -------------------------------------------------
        # Configure Docling PDF pipeline
        # -------------------------------------------------

        pipeline_options = PdfPipelineOptions()

        # Generate images for figures/pictures
        pipeline_options.generate_picture_images = True

        # Keep page images available as well
        pipeline_options.generate_page_images = True

        pipeline_options.images_scale = 2.0

        # -------------------------------------------------
        # Create converter
        # -------------------------------------------------

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )

        # -------------------------------------------------
        # Convert document
        # -------------------------------------------------

        result = converter.convert(
            file_path
        )

        return result.document

    except Exception as exc:
        raise PaperProcessingException(
            f"Failed to parse document: {exc}"
        ) from exc


# ---------------------------------------------------------
# Text Extraction
# ---------------------------------------------------------


def extract_text_items(
    document,
) -> list[dict[str, Any]]:
    """
    Extract text elements from a DoclingDocument.

    Each text item contains:

        - text
        - type
        - label
        - page_number

    Returns:
        List of structured text items.
    """

    text_items = []

    for item in document.texts:

        page_number = None

        if item.prov:
            page_number = item.prov[0].page_no

        text_items.append(
            {
                "text": item.text,
                "type": type(item).__name__,
                "label": str(item.label),
                "page_number": page_number,
            }
        )

    return text_items


# ---------------------------------------------------------
# Table Extraction
# ---------------------------------------------------------

def extract_tables(
    document,
) -> list[dict[str, Any]]:
    """
    Extract tables from a DoclingDocument.

    Each table contains:

        - table_number
        - caption
        - page_number
        - headers
        - rows
        - markdown

    Returns:
        List of structured tables.
    """

    tables = []

    for index, table in enumerate(
        document.tables,
        start=1,
    ):

        # -------------------------------------------------
        # Page number
        # -------------------------------------------------

        page_number = None

        if table.prov:
            page_number = table.prov[0].page_no

        # -------------------------------------------------
        # Caption
        # -------------------------------------------------

        caption = table.caption_text(
            document
        )

        # -------------------------------------------------
        # Markdown representation
        # -------------------------------------------------

        markdown = table.export_to_markdown(
            doc=document
        )

        # -------------------------------------------------
        # Structured table data
        # -------------------------------------------------

        headers = []
        rows = []

        try:
            dataframe = table.export_to_dataframe()

            if dataframe is not None:

                headers = [
                    str(column)
                    for column in dataframe.columns
                ]

                rows = [
                    [
                        (
                            None
                            if value is None
                            else str(value)
                        )
                        for value in row
                    ]
                    for row in dataframe.values.tolist()
                ]

        except Exception as exc:

            print(
                f"Could not convert Table {index} "
                f"to structured data: {exc}"
            )

        # -------------------------------------------------
        # Store table information
        # -------------------------------------------------

        tables.append(
            {
                "table_number": index,
                "caption": caption,
                "page_number": page_number,
                "headers": headers,
                "rows": rows,
                "markdown": markdown,
            }
        )

    return tables

# ---------------------------------------------------------
# Figure / Picture Extraction
# ---------------------------------------------------------

def extract_figures(
    document,
) -> list[dict[str, Any]]:
    """
    Extract figures/pictures from a DoclingDocument.

    Figures are kept in memory as PIL Image objects.
    They are not saved to the local filesystem.

    Args:
        document:
            DoclingDocument returned by parse_document().

    Returns:
        List of dictionaries containing figure metadata
        and the extracted image.
    """

    figures = []

    for index, picture in enumerate(
        document.pictures,
        start=1,
    ):
        page_number = None

        if picture.prov:
            page_number = picture.prov[0].page_no

        caption = picture.caption_text(
            document
        )

        image = None

        try:
            image = picture.get_image(
                document
            )

        except Exception as exc:
            print(
                f"Could not extract image "
                f"for Figure {index}: {exc}"
            )

        if image is not None:
            print(
                f"Figure {index} extracted: "
                f"{image.width} x {image.height}"
            )
        else:
            print(
                f"Figure {index}: "
                f"image not available"
            )

        figures.append(
            {
                "figure_number": index,
                "caption": caption,
                "page_number": page_number,
                "image": image,
            }
        )

    return figures

# ---------------------------------------------------------
# Complete Structured Extraction
# ---------------------------------------------------------


def extract_document_content(
    document,
) -> dict[str, Any]:
    """
    Extract the main structured content
    from a DoclingDocument.

    Returns:

        {
            "text_items": [...],
            "tables": [...],
            "figures": [...]
        }
    """

    return {
        "text_items": extract_text_items(
            document
        ),
        "tables": extract_tables(
            document
        ),
        "figures": extract_figures(
            document
        ),
    }


# ---------------------------------------------------------
# Manual Smoke Test
# ---------------------------------------------------------


if __name__ == "__main__":

    file_path = (
        "data/test_pdfs/sample.pdf"
    )

    print("=" * 60)
    print("DOCUMENT PARSER TEST")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1: Parse PDF
    # -----------------------------------------------------

    document = parse_document(
        file_path
    )

    print("\nDocument parsed successfully!")

    print(
        "Document type:",
        type(document),
    )

    # -----------------------------------------------------
    # Step 2: Extract structured content
    # -----------------------------------------------------

    content = extract_document_content(
        document
    )

    # -----------------------------------------------------
    # Step 3: Print summary
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    print(
        "\nText items:",
        len(content["text_items"]),
    )

    print(
        "Tables:",
        len(content["tables"]),
    )

    print(
        "Figures:",
        len(content["figures"]),
    )

    # -----------------------------------------------------
    # Step 4: Show first few text items
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("FIRST 5 TEXT ITEMS")
    print("=" * 60)

    for item in content["text_items"][:5]:

        print(
            f"\nType: {item['type']}"
        )

        print(
            f"Label: {item['label']}"
        )

        print(
            f"Page: {item['page_number']}"
        )

        print(
            f"Text: {item['text']}"
        )

    # -----------------------------------------------------
    # Step 5: Show tables
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("TABLE SUMMARY")
    print("=" * 60)

    for table in content["tables"]:

        print(
            f"\nTable {table['table_number']}"
        )

        print(
            f"Page: {table['page_number']}"
        )

        print(
            f"Caption: {table['caption']}"
        )

        print(
            "\nHeaders:"
        )

        print(
            table["headers"]
        )

        print(
            "\nRows:"
        )

        for row in table["rows"]:
            print(row)

        print(
            "\nOriginal Markdown:"
        )

        print(
            table["markdown"]
        )

    # -----------------------------------------------------
    # Step 6: Show figures
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("FIGURE SUMMARY")
    print("=" * 60)

    for figure in content["figures"]:

        image_status = (
            "available"
            if figure["image"] is not None
            else "not available"
        )

        print(
            f"\nFigure {figure['figure_number']}"
        )

        print(
            f"Page: {figure['page_number']}"
        )

        print(
            f"Caption: {figure['caption']}"
        )

        print(
            f"Image: {image_status}"
        )

    print("\n" + "=" * 60)
    print("PARSER TEST COMPLETED")
    print("=" * 60)