import os
from pinecone import Pinecone

class PineconeVectorStore:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)
        self.namespace = "default"  # default namespace

        # Determine the field name used for text in the index's field_map
        # Usually "text" or "chunk_text". We default to "text".
        # You can adjust this if your index uses a different field.
        self.text_field = "text"

    def add_chunks(self, chunks: list[dict], workspace_id: str, user_id: str, document_urls: dict = None) -> None:
        """
        Upsert records for an integrated embedding index.
        Each record must have:
            - _id (str)
            - a text field matching the index's field_map (default "text")
            - other metadata fields as top-level keys
        """
        records = []
        for chunk in chunks:
            unique_id = f"{workspace_id}_{chunk['chunk_id']}"
            doc_url = document_urls.get(chunk['document_id'], '') if document_urls else ''
            record = {
                "_id": unique_id,
                self.text_field: chunk["text"],          # text field for embedding
                "document_id": chunk["document_id"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "workspace_id": workspace_id,
                "user_id": user_id,
                "document_url": doc_url,
            }
            records.append(record)

        batch_size = 50
        for i in range(0, len(records), batch_size):
            self.index.upsert_records(
                namespace=self.namespace,
                records=records[i:i + batch_size]
            )

    def search(self, query_text: str, workspace_id: str, top_k: int = 5) -> list[dict]:
        """
        Search using raw text query; Pinecone auto-embeds the query.
        """
        query = {
            "inputs": {self.text_field: query_text},   # use same text field
            "top_k": top_k,
            "filter": {"workspace_id": workspace_id},
        }

        response = self.index.search_records(
            namespace=self.namespace,
            query=query
        )

        # Response can be dict or object depending on SDK version
        if isinstance(response, dict):
            result = response.get("result", {})
            hits = result.get("hits", [])
        else:
            result = getattr(response, "result", None)
            hits = getattr(result, "hits", []) if result else []

        results = []
        for hit in hits:
            # hit is dict or object
            if isinstance(hit, dict):
                hit_id = hit.get("_id")
                score = hit.get("_score")
                fields = hit.get("fields", {})
            else:
                hit_id = getattr(hit, "_id", None)
                score = getattr(hit, "_score", None)
                fields = getattr(hit, "fields", {})

            # Build result dict from fields plus id and score
            result_item = {
                "chunk_id": hit_id,
                "score": score,
            }
            # Merge fields (which contain document_id, page_start, etc.)
            if isinstance(fields, dict):
                result_item.update(fields)
            else:
                # If fields is object, convert to dict
                fields_dict = {}
                for key in dir(fields):
                    if not key.startswith("_"):
                        try:
                            fields_dict[key] = getattr(fields, key)
                        except:
                            pass
                result_item.update(fields_dict)

            results.append(result_item)

        return results

    def delete_by_workspace(self, workspace_id: str) -> None:
        """Delete all records for a workspace."""
        self.index.delete_records(
            namespace=self.namespace,
            filter={"workspace_id": workspace_id}
        )

    def delete_by_document(self, workspace_id: str, document_id: str) -> None:
        """Delete records for a specific document within a workspace."""
        self.index.delete_records(
            namespace=self.namespace,
            filter={
                "workspace_id": workspace_id,
                "document_id": document_id
            }
        )