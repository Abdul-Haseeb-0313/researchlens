import os
from pinecone import Pinecone

class PineconeVectorStore:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.index = self.pc.Index(self.index_name)

    def add_chunks(self, chunks: list[dict], workspace_id: str, user_id: str, document_urls: dict = None) -> None:
        vectors = []
        for chunk in chunks:
            unique_id = f"{workspace_id}_{chunk['chunk_id']}"
            doc_url = document_urls.get(chunk['document_id'], '') if document_urls else ''
            vectors.append({
                "id": unique_id,
                "values": chunk["embedding"],
                "metadata": {
                    "document_id": chunk["document_id"],
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                    "text": chunk["text"],
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "document_url": doc_url
                }
            })

        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            self.index.upsert(vectors=vectors[i:i+batch_size])

    def search(self, query_embedding: list[float], workspace_id: str, top_k: int = 5) -> list[dict]:
        response = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter={"workspace_id": workspace_id},
        )
        results = []
        for match in response.matches:
            results.append({
                "chunk_id": match.id,
                "score": match.score,
                **match.metadata,
            })
        return results

    def delete_by_workspace(self, workspace_id: str) -> None:
        """Delete all vectors belonging to a workspace."""
        self.index.delete(filter={"workspace_id": workspace_id})

    def delete_by_document(self, workspace_id: str, document_id: str) -> None:
        """Delete all vectors belonging to a specific document within a workspace."""
        self.index.delete(filter={
            "workspace_id": workspace_id,
            "document_id": document_id
        })