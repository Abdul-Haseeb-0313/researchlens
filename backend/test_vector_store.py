from app.ingestion.pdf_loader import load_pdf
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import create_chunks
from app.retrieval.embeddings import EmbeddingModel
from app.retrieval.vector_store import VectorStore


PDF_PATH = "../documents/sample.pdf"


# --------------------------------------------------
# 1. Load PDF
# --------------------------------------------------

raw_pages = load_pdf(PDF_PATH)


# --------------------------------------------------
# 2. Clean pages
# --------------------------------------------------

cleaned_pages = [
    {
        "page": page["page"],
        "text": clean_text(page["text"]),
    }
    for page in raw_pages
]


# --------------------------------------------------
# 3. Create chunks
# --------------------------------------------------

chunks = create_chunks(
    cleaned_pages,
    document_id="sample",
)

print(f"Created {len(chunks)} chunks.")


# --------------------------------------------------
# 4. Generate embeddings
# --------------------------------------------------

embedder = EmbeddingModel()

embedded_chunks = embedder.embed_chunks(chunks)

print(f"Generated {len(embedded_chunks)} embeddings.")


# --------------------------------------------------
# 5. Create FAISS vector store
# --------------------------------------------------

dimension = len(embedded_chunks[0]["embedding"])

vector_store = VectorStore(dimension)

vector_store.add_chunks(embedded_chunks)

print(f"FAISS vectors: {vector_store.index.ntotal}")


# --------------------------------------------------
# 6. Search
# --------------------------------------------------

question = "Does this guy have anything related to Intelligent Systems?"

query_embedding = embedder.embed_text(question)

results = vector_store.search(
    query_embedding,
    top_k=5,
)


# --------------------------------------------------
# 7. Display results
# --------------------------------------------------

print("\n" + "=" * 80)
print("SEARCH RESULTS")
print("=" * 80)

for rank, result in enumerate(results, start=1):

    print(f"\n--- Result {rank} ---")

    print(f"Score: {result['score']:.4f}")

    print(f"Chunk: {result['chunk_id']}")

    print(
        f"Pages: "
        f"{result['page_start']} - "
        f"{result['page_end']}"
    )

    print("\nText:")
    print(result["text"][:700])