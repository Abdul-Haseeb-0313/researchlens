from app.retrieval.embeddings import EmbeddingModel


embedder = EmbeddingModel()

text = "The Transformer architecture uses self-attention mechanisms."

embedding = embedder.embed_text(text)

print(f"Embedding dimensions: {len(embedding)}")
print(f"First 10 values: {embedding[:10]}")