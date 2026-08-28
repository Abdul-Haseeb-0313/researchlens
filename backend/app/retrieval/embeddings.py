from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

class EmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)

    def embed_text(self, text: str) -> list[float]:
        """
        Convert a single piece of text into an embedding vector.
        """

        if not text.strip():
            raise ValueError("Cannot embed empty text.")

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_chunks(self, chunks: list[dict]) -> list[dict]:
        """
        Generate embeddings for all document chunks while
        preserving their existing metadata.
        """

        if not chunks:
            return []

        texts = [chunk["text"] for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        embedded_chunks = []

        for chunk, embedding in zip(chunks, embeddings):
            embedded_chunks.append(
                {
                    **chunk,
                    "embedding": embedding.tolist(),
                }
            )

        return embedded_chunks