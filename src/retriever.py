from __future__ import annotations

from collections.abc import Iterable


def tokenize(text: str) -> list[str]:
    try:
        import jieba

        return [token.strip() for token in jieba.cut(text) if token.strip()]
    except Exception:  # pragma: no cover
        return [char for char in text if not char.isspace()]


class BM25Retriever:
    def __init__(self, chunks: Iterable):
        self.chunks = list(chunks)
        self.tokenized = [tokenize(getattr(chunk, "text", str(chunk))) for chunk in self.chunks]
        try:
            from rank_bm25 import BM25Okapi

            self._bm25 = BM25Okapi(self.tokenized)
        except Exception:  # pragma: no cover
            self._bm25 = None

    def search(self, query: str, top_k: int = 6):
        if not self.chunks:
            return []
        tokens = tokenize(query)
        if self._bm25:
            scores = self._bm25.get_scores(tokens)
            ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
            return [(self.chunks[index], float(score)) for index, score in ranked]

        token_set = set(tokens)
        ranked = []
        for index, doc_tokens in enumerate(self.tokenized):
            if not doc_tokens:
                score = 0.0
            else:
                score = len(token_set.intersection(doc_tokens)) / max(len(token_set), 1)
            ranked.append((index, score))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return [(self.chunks[index], float(score)) for index, score in ranked[:top_k]]

