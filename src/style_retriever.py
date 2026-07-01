from __future__ import annotations

from .md_exam_loader import ExamBank, StyleExample
from .retriever import BM25Retriever


class StyleRetriever:
    def __init__(self, banks: list[ExamBank]):
        self.examples: list[StyleExample] = [example for bank in banks for example in bank.examples]
        self._retriever = BM25Retriever(self.examples)

    def search(self, query: str, question_type: str | None = None, top_k: int = 5) -> list[tuple[StyleExample, float]]:
        pool = self.examples
        if question_type:
            pool = [example for example in pool if example.question_type == question_type]
        if not pool:
            return []
        retriever = BM25Retriever(pool)
        return retriever.search(query, top_k=top_k)

