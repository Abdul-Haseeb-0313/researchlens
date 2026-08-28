from app.ingestion.pdf_loader import load_pdf
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import create_chunks
from app.retrieval.embeddings import EmbeddingModel
from app.retrieval.vector_store import VectorStore
from app.retrieval.reranker import Reranker
from app.generation.llm import GeminiLLM
from app.services.rag import RAGPipeline

# 1. Load and process PDF
raw_pages = load_pdf("../documents/sample.pdf")
cleaned_pages = [{"page": p["page"], "text": clean_text(p["text"])} for p in raw_pages]
chunks = create_chunks(cleaned_pages, document_id="sample")

# 2. Embed and index
embedder = EmbeddingModel()
embedded_chunks = embedder.embed_chunks(chunks)
vector_store = VectorStore(len(embedded_chunks[0]["embedding"]))
vector_store.add_chunks(embedded_chunks)

# 3. Reranker and LLM
reranker = Reranker()
llm = GeminiLLM()

# 4. Build pipeline
rag = RAGPipeline(embedder, vector_store, reranker, llm)

# 5. Ask a question
question = "What is the main idea of this document?"
result = rag.answer(question, retrieval_k=10, final_k=5)

print("ANSWER:\n", result["answer"])
print("\nCITED SOURCES:")
for i, src in enumerate(result["cited_sources"], 1):
    print(f"  [{i}] {src['document_id']} pages {src['page_start']}-{src['page_end']}")