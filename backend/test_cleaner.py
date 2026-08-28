from app.ingestion.pdf_loader import load_pdf
from app.ingestion.cleaner import clean_text


pdf_path = "../documents/sample.pdf"

pages = load_pdf(pdf_path)

for page in pages[:3]:
    cleaned = clean_text(page["text"])

    print(f"\n--- Page {page['page']} ---")
    print(cleaned[:1500])