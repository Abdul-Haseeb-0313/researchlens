from pathlib import Path
from .pdf_loader import load_pdf
from .cleaner import clean_text
from .chunker import create_chunks


def process_pdfs(pdf_paths: list[str]) -> list[dict]:
    """
    Process multiple PDFs and return a combined list of chunks.
    Each chunk's document_id is derived from the PDF filename (without extension).
    """
    all_chunks = []
    for path_str in pdf_paths:
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path_str}")

        doc_id = path.stem  # e.g. "sample" from "sample.pdf"
        raw_pages = load_pdf(path_str)
        cleaned_pages = [
            {"page": p["page"], "text": clean_text(p["text"])}
            for p in raw_pages
        ]
        chunks = create_chunks(cleaned_pages, document_id=doc_id)
        all_chunks.extend(chunks)

    return all_chunks