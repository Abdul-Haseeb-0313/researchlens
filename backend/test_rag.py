from app.ingestion.pdf_loader import load_pdf
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import create_chunks

from app.retrieval.embeddings import EmbeddingModel
from app.retrieval.vector_store import VectorStore
from app.retrieval.reranker import Reranker

from app.generation.llm import GeminiLLM
from app.services.rag import RAGPipeline


# ==================================================
# CONFIGURATION
# ==================================================

PDF_PATH = "../documents/sample.pdf"

DOCUMENT_ID = "sample"


# ==================================================
# 1. LOAD PDF
# ==================================================

print("\n[1/7] Loading PDF...")

raw_pages = load_pdf(PDF_PATH)

print(f"Loaded {len(raw_pages)} pages.")


# ==================================================
# 2. CLEAN TEXT
# ==================================================

print("\n[2/7] Cleaning text...")

cleaned_pages = [
    {
        "page": page["page"],
        "text": clean_text(page["text"]),
    }
    for page in raw_pages
]


# ==================================================
# 3. CREATE CHUNKS
# ==================================================

print("\n[3/7] Creating chunks...")

chunks = create_chunks(
    cleaned_pages,
    document_id=DOCUMENT_ID,
)

print(f"Created {len(chunks)} chunks.")


# ==================================================
# 4. CREATE EMBEDDINGS
# ==================================================

print("\n[4/7] Generating embeddings...")

embedder = EmbeddingModel()

embedded_chunks = embedder.embed_chunks(
    chunks
)

print(
    f"Generated {len(embedded_chunks)} embeddings."
)


# ==================================================
# 5. CREATE FAISS INDEX
# ==================================================

print("\n[5/7] Building FAISS index...")

dimension = len(
    embedded_chunks[0]["embedding"]
)

vector_store = VectorStore(
    dimension
)

vector_store.add_chunks(
    embedded_chunks
)

print(
    f"FAISS contains "
    f"{vector_store.index.ntotal} vectors."
)


# ==================================================
# 6. INITIALIZE RERANKER + GEMINI
# ==================================================

print("\n[6/7] Loading reranker and Gemini...")

reranker = Reranker()

llm = GeminiLLM()


# ==================================================
# 7. BUILD AND RUN RAG
# ==================================================

print("\n[7/7] Running RAG pipeline...")

rag = RAGPipeline(
    embedder=embedder,
    vector_store=vector_store,
    reranker=reranker,
    llm=llm,
)


question = "What is the main idea of this document?"


result = rag.answer(
    question,
    retrieval_k=10,
    final_k=5,
)


# ==================================================
# DISPLAY ANSWER
# ==================================================

print("\n")
print("=" * 80)
print("RESEARCHLENS ANSWER")
print("=" * 80)

print(result["answer"])


# ==================================================
# DISPLAY SOURCES
# ==================================================

print("\n")
print("=" * 80)
print("SOURCES")
print("=" * 80)

for index, source in enumerate(
    result["sources"],
    start=1,
):

    print(
        f"\n[{index}] "
        f"{source['document_id']} "
        f"| Pages "
        f"{source['page_start']}-"
        f"{source['page_end']}"
    )

    print(
        f"FAISS score: "
        f"{source['score']:.4f}"
    )

    print(
        f"Rerank score: "
        f"{source['rerank_score']:.4f}"
    )

    print(
        f"\n{source['text'][:500]}..."
    )