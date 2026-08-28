from typing import Iterable


def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    Args:
        text: Cleaned document text.
        chunk_size: Approximate number of words per chunk.
        overlap: Number of overlapping words between chunks.

    Returns:
        A list of text chunks.
    """

    if not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    words = text.split()

    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]

        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))

        if start + chunk_size >= len(words):
            break

    return chunks


def create_chunks(
    pages: Iterable[dict],
    document_id: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[dict]:
    """
    Create metadata-aware chunks from cleaned PDF pages.

    Each chunk keeps track of its source document and page.
    """

    chunks = []
    chunk_number = 1

    for page in pages:
        page_number = page["page"]
        text = page["text"]

        page_chunks = split_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for chunk_text in page_chunks:
            chunks.append(
                {
                    "chunk_id": f"{document_id}_chunk_{chunk_number:04d}",
                    "document_id": document_id,
                    "page_start": page_number,
                    "page_end": page_number,
                    "text": chunk_text,
                }
            )

            chunk_number += 1

    return chunks