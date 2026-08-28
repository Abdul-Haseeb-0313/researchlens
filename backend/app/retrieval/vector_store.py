import json
import numpy as np
import faiss


class VectorStore:
    def __init__(self, dimension: int):
        """
        Create a FAISS index for normalized embeddings.

        Inner product is equivalent to cosine similarity
        when vectors are normalized.
        """

        self.index = faiss.IndexFlatIP(dimension)
        self.chunks = []

    def add_chunks(self, chunks: list[dict]) -> None:
        """
        Add embedded chunks to the FAISS index.
        """

        if not chunks:
            return

        embeddings = np.array(
            [chunk["embedding"] for chunk in chunks],
            dtype="float32",
        )

        self.index.add(embeddings)
        self.chunks.extend(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search for the most semantically similar chunks.
        """

        if self.index.ntotal == 0:
            return []

        query_vector = np.array(
            [query_embedding],
            dtype="float32",
        )

        scores, indices = self.index.search(
            query_vector,
            min(top_k, self.index.ntotal),
        )

        results = []

        for score, index in zip(scores[0], indices[0]):
            chunk = self.chunks[index].copy()
            chunk["score"] = float(score)
            results.append(chunk)

        return results

    def save(self, index_path: str, chunks_path: str):
        """Save the FAISS index and chunk metadata to disk."""
        faiss.write_index(self.index, index_path)
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, indent=2)

    @classmethod
    def load(cls, index_path: str, chunks_path: str):
        """Load a saved FAISS index and chunk metadata."""
        index = faiss.read_index(index_path)
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        obj = cls.__new__(cls)
        obj.index = index
        obj.chunks = chunks
        return obj