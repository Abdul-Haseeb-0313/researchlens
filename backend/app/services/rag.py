import re
from typing import List, Dict, Any, Optional


def _extract_citations(answer: str, max_source: int) -> List[int]:
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, answer)
    seen = set()
    citations = []
    for match in matches:
        num = int(match)
        if 1 <= num <= max_source and num not in seen:
            seen.add(num)
            citations.append(num)
    return citations


def _clean_answer(answer: str, max_source: int) -> str:
    """Remove citation markers that reference non-existent sources."""
    def repl(match):
        num = int(match.group(1))
        return match.group(0) if 1 <= num <= max_source else ""
    return re.sub(r'\[(\d+)\]', repl, answer)


def _is_greeting(question: str) -> bool:
    """Simple heuristic to detect greetings / small talk."""
    greetings = {
        "hi", "hello", "hey", "good morning", "good afternoon",
        "good evening", "thanks", "thank you", "how are you",
        "what's up", "whats up", "who are you", "what can you do",
    }
    q = question.lower().strip().rstrip("?!. ")
    # Check exact match or short sentence consisting solely of greeting words
    words = q.split()
    if len(words) <= 4 and any(g in q for g in greetings):
        return True
    return False


def build_context(chunks: list[dict]) -> str:
    sections = []
    for index, chunk in enumerate(chunks, start=1):
        section = (
            f"SOURCE {index}\n"
            f"Document: {chunk['document_id']}\n"
            f"Pages: {chunk['page_start']}-{chunk['page_end']}\n\n"
            f"{chunk['text']}"
        )
        sections.append(section)
    return ("\n\n" + ("\n\n" + "-" * 60 + "\n\n").join(sections))


class RAGPipeline:
    def __init__(self, embedder, vector_store, reranker, llm):
        self.embedder = embedder
        self.vector_store = vector_store
        self.reranker = reranker
        self.llm = llm

    def answer(
        self,
        question: str,
        retrieval_k: int = 10,
        final_k: int = 5,
        workspace_id: str = None,
        reformulated_question: Optional[str] = None,
        history: Optional[List[dict]] = None,
    ) -> dict:
        # Greeting / small talk → bypass retrieval
        if _is_greeting(question):
            return {
                "answer": "Hello! I'm ResearchLens. Ask me anything about your uploaded documents and I'll provide cited answers.",
                "sources": [],
                "cited_sources": [],
            }

        retrieval_query = reformulated_question or question

        # 1. Embed retrieval query
        query_embedding = self.embedder.embed_text(retrieval_query)

        # 2. Retrieve candidates
        if workspace_id:
            candidates = self.vector_store.search(
                query_embedding,
                workspace_id=workspace_id,
                top_k=retrieval_k,
            )
        else:
            candidates = self.vector_store.search(query_embedding, top_k=retrieval_k)

        if not candidates:
            return {
                "answer": "I couldn't find any relevant information in the documents.",
                "sources": [],
                "cited_sources": [],
            }

        # 3. Rerank
        reranked = self.reranker.rerank(retrieval_query, candidates, top_k=final_k)

        # 4. Build context
        context = build_context(reranked)

        # 5. Conversation history
        history_str = ""
        if history:
            history_parts = []
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_str = "\n".join(history_parts[-6:])

        # 6. Prompt
        prompt = f"""
You are ResearchLens, an evidence‑grounded research assistant.

Answer the user's question using ONLY the provided evidence and conversation history.

STRICT RULES:
1. Cite your sources inline using square brackets with the source number, e.g. [1] or [2].
2. Only cite sources that actually support the statement.
3. You may cite multiple sources in one sentence if needed, like [1][2].
4. Do NOT invent any facts or sources.
5. If the evidence is insufficient, say: "I couldn't find enough evidence in the uploaded documents."
6. Be concise but informative.
7. The source numbers correspond to the SOURCE numbers in the evidence below.

CONVERSATION HISTORY:
{history_str if history_str else "None"}

EVIDENCE:

{context}

USER QUESTION:

{question}

ANSWER (with citations):
"""

        # 7. Generate answer
        raw_answer = self.llm.generate(prompt)

        # 8. Sanitize citations
        max_src = len(reranked)
        clean_answer = _clean_answer(raw_answer, max_src)

        # 9. Extract cited sources
        cited_numbers = _extract_citations(clean_answer, max_source=max_src)
        cited_sources = [reranked[i - 1] for i in cited_numbers]

        return {
            "answer": clean_answer,
            "sources": reranked,
            "cited_sources": cited_sources,
        }