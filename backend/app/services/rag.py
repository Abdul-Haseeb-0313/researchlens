import re
from typing import List, Dict, Any, Optional


def _extract_citation_numbers(answer: str, max_source: int) -> List[int]:
    """
    Extract all valid citation numbers from inline markers.
    Handles single [1], multiple [2,3], and mixed [1, 4] forms.
    Returns numbers in the order they appear.
    """
    pattern = r'\[([\d,\s]+)\]'
    matches = re.findall(pattern, answer)
    seen = set()
    numbers = []
    for match in matches:
        for part in match.split(','):
            part = part.strip()
            if part.isdigit():
                num = int(part)
                if 1 <= num <= max_source and num not in seen:
                    seen.add(num)
                    numbers.append(num)
    return numbers


def _clean_answer(answer: str, max_source: int) -> str:
    """
    Remove citation markers that reference non-existent sources.
    Keep valid numbers (including comma-separated) and preserve formatting.
    """
    def repl(match):
        content = match.group(1)
        valid_parts = []
        for part in content.split(','):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= max_source:
                valid_parts.append(part)
        if valid_parts:
            # Keep original formatting: just join with comma+space
            return "[" + ", ".join(valid_parts) + "]"
        else:
            return ""
    return re.sub(r'\[([\d,\s]+)\]', repl, answer)


def _strip_citation_list(answer: str) -> str:
    """
    Remove any trailing lines that start with [n] followed by a space.
    Those are a separate sources list the model may have added.
    """
    lines = answer.strip().split("\n")
    cleaned = []
    for line in lines:
        if re.match(r'^\s*\[\d+\]\s+', line):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def _is_greeting(question: str) -> bool:
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon",
                 "thanks", "thank you", "how are you", "what's up", "whats up"}
    q = question.lower().strip().rstrip("?!. ")
    return any(g in q for g in greetings) and len(q.split()) <= 4


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


def _build_sources_block(cited_info: List[dict]) -> str:
    """
    Build a Sources: block from a list of {citation_number, chunk} dicts.
    The citation_number is the actual number used inline.
    """
    if not cited_info:
        return ""
    lines = ["", "Sources:"]
    for item in cited_info:
        num = item["citation_number"]
        src = item["chunk"]
        doc = src.get("document_id", "Unknown")
        page = src.get("page_start", "?")
        lines.append(f"[{num}] {doc}, page {page}")
    return "\n".join(lines)


class RAGPipeline:
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm

    def answer(
        self,
        question: str,
        retrieval_k: int = 10,
        final_k: int = 5,
        workspace_id: str = None,
        history: Optional[List[dict]] = None,
    ) -> dict:
        if _is_greeting(question):
            return {
                "answer": "Hello! I'm ResearchLens. Ask me anything about your uploaded documents and I'll provide cited answers.",
                "sources": [],
                "cited_sources": [],
            }

        candidates = self.vector_store.search(
            question,
            workspace_id=workspace_id,
            top_k=retrieval_k,
        )
        if not candidates:
            return {
                "answer": "I couldn't find any relevant information in the documents.",
                "sources": [],
                "cited_sources": [],
            }

        final_chunks = candidates[:final_k]
        max_src = len(final_chunks)
        context = build_context(final_chunks)

        history_str = ""
        if history:
            parts = []
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                parts.append(f"{role}: {msg['content']}")
            history_str = "\n".join(parts[-6:])

        prompt = f"""
You are ResearchLens, an evidence‑grounded research assistant.

Answer the user's question using ONLY the provided evidence and conversation history.

STRICT RULES:
1. There are exactly {max_src} sources available, numbered 1 to {max_src}.
2. Use inline citations ONLY, like [1] or [2] immediately after the relevant sentence.
3. You may cite multiple sources in one bracket, e.g. [1,3].
4. Never cite a source number greater than {max_src}.
5. Do NOT include a separate "Sources" section at the end.
6. Do not list sources as [1] DocumentName · p.X at the bottom.
7. If evidence is insufficient, say: "I couldn't find enough evidence in the uploaded documents."

CONVERSATION HISTORY:
{history_str if history_str else "None"}

EVIDENCE:

{context}

USER QUESTION:

{question}

ANSWER (with inline citations only):
"""

        raw_answer = self.llm.generate(prompt)
        answer = _clean_answer(raw_answer, max_src)
        answer = _strip_citation_list(answer)

        # Extract citation numbers (order preserved)
        cited_numbers = _extract_citation_numbers(answer, max_src)

        # Build cited_info list: unique numbers with their chunk
        cited_info = []
        seen = set()
        for num in cited_numbers:
            if num in seen:
                continue
            seen.add(num)
            chunk = final_chunks[num - 1]
            cited_info.append({
                "citation_number": num,
                "chunk": chunk,
            })

        # Build the sources block
        sources_block = _build_sources_block(cited_info)
        if sources_block:
            answer = answer + "\n" + sources_block

        # Prepare cited_sources for API response (with citation_number)
        cited_sources = [
            {**item["chunk"], "citation_number": item["citation_number"]}
            for item in cited_info
        ]

        return {
            "answer": answer,
            "sources": final_chunks,
            "cited_sources": cited_sources,
        }