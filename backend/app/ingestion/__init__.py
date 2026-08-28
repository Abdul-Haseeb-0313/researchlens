from pathlib import Path

import fitz


def load_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF page-by-page.

    Returns:
        A list of dictionaries containing:
        - page: 1-based page number
        - text: extracted text
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF.")

    pages = []

    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")

            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages