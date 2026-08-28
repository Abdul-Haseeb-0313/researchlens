from app.ingestion.pdf_loader import load_pdf
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import create_chunks


pdf_path = "../documents/sample.pdf"

raw_pages = load_pdf(pdf_path)

cleaned_pages = [
    {
        "page": page["page"],
        "text": clean_text(page["text"]),
    }
    for page in raw_pages
]

chunks = create_chunks(
    cleaned_pages,
    document_id="sample",
)

print(f"Total chunks: {len(chunks)}")

for chunk in chunks:
    print("\n" + "=" * 80)
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Pages: {chunk['page_start']} - {chunk['page_end']}")
    print(f"Words: {len(chunk['text'].split())}")
    print(chunk["text"])