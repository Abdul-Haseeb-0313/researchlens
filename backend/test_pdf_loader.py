from app.ingestion.pdf_loader import load_pdf


pdf_path = "../documents/sample.pdf"

pages = load_pdf(pdf_path)

print(f"Total pages: {len(pages)}")

for page in pages[:3]:
    print(f"\n--- Page {page['page']} ---")
    print(page["text"][:1000])