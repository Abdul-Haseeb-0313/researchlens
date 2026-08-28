from app.ingestion.pdf_loader import load_pdf
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import create_chunks
from app.retrieval.embeddings import EmbeddingModel
from app.retrieval.vector_store import VectorStore
from app.retrieval.reranker import Reranker


PDF_PATH = "../documents/sample.pdf"


# --------------------------------------------------
# 1. Load PDF
# --------------------------------------------------

raw_pages = load_pdf(PDF_PATH)


# --------------------------------------------------
# 2. Clean
# --------------------------------------------------

cleaned_pages = [
    {
        "page": page["page"],
        "text": clean_text(page["text"]),
    }
    for page in raw_pages
]


# --------------------------------------------------
# 3. Chunk
# --------------------------------------------------

chunks = create_chunks(
    cleaned_pages,
    document_id="sample",
)

print(f"Created {len(chunks)} chunks.")


# --------------------------------------------------
# 4. Embed
# --------------------------------------------------

embedder = EmbeddingModel()

embedded_chunks = embedder.embed_chunks(chunks)


# --------------------------------------------------
# 5. FAISS
# --------------------------------------------------

dimension = len(
    embedded_chunks[0]["embedding"]
)

vector_store = VectorStore(dimension)

vector_store.add_chunks(
    embedded_chunks
)


# --------------------------------------------------
# 6. Retrieve candidates
# --------------------------------------------------

question = "What is the main idea of this paper?"

query_embedding = embedder.embed_text(
    question
)

retrieved = vector_store.search(
    query_embedding,
    top_k=10,
)

print("\nFAISS RESULTS")

for result in retrieved:
    print(
        f"{result['score']:.4f} | "
        f"Page {result['page_start']}"
    )


# --------------------------------------------------
# 7. Rerank
# --------------------------------------------------

reranker = Reranker()

reranked = reranker.rerank(
    question,
    retrieved,
    top_k=5,
)


# --------------------------------------------------
# 8. Display reranked results
# --------------------------------------------------

print("\n" + "=" * 80)
print("RERANKED RESULTS")
print("=" * 80)

for rank, result in enumerate(
    reranked,
    start=1,
):

    print(f"\n--- Result {rank} ---")

    print(
        f"FAISS score: "
        f"{result['score']:.4f}"
    )

    print(
        f"Rerank score: "
        f"{result['rerank_score']:.4f}"
    )

    print(
        f"Page: "
        f"{result['page_start']}"
    )

    print(
        f"\n{result['text'][:700]}"
    )