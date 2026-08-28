from app.ingestion.service import process_pdfs
from app.retrieval.embeddings import EmbeddingModel
from app.retrieval.vector_store import VectorStore
from app.retrieval.reranker import Reranker
from app.generation.llm import GeminiLLM
from app.services.rag import RAGPipeline

# ---- 1. Ingest multiple PDFs ----
# Use two different PDFs. For this test, I'll use the same file twice,
# but you can replace with actual different PDFs.
pdf_list = [
    "../documents/sample.pdf",
    "../documents/sample2.pdf",   # duplicate to simulate second document
]
chunks = process_pdfs(pdf_list)
print(f"Total chunks from {len(pdf_list)} documents: {len(chunks)}")

# Verify unique document IDs
doc_ids = set(chunk['document_id'] for chunk in chunks)
print("Document IDs found:", doc_ids)

# ---- 2. Embed all chunks at once ----
embedder = EmbeddingModel()
embedded_chunks = embedder.embed_chunks(chunks)

# ---- 3. Build FAISS index ----
dimension = len(embedded_chunks[0]["embedding"])
vector_store = VectorStore(dimension)
vector_store.add_chunks(embedded_chunks)

# ---- 4. Reranker & LLM ----
reranker = Reranker()
llm = GeminiLLM()

# ---- 5. Build RAG pipeline ----
rag = RAGPipeline(embedder, vector_store, reranker, llm)

# ---- 6. Ask a question ----
question = "what best suits for him? Teacher or SDE? and what could make him more money?"
result = rag.answer(question, retrieval_k=10, final_k=5)

print("\nANSWER:\n", result["answer"])
print("\nCITED SOURCES:")
for i, src in enumerate(result["cited_sources"], 1):
    print(f"  [{i}] Document: {src['document_id']}, pages {src['page_start']}-{src['page_end']}")