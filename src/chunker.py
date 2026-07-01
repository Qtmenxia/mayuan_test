from __future__ import annotations

import re

from pydantic import BaseModel

from .pdf_loader import PageText


class KnowledgeChunk(BaseModel):
    chunk_id: str
    page_start: int
    page_end: int
    section_path: str
    text: str


HEADING_PATTERNS = [
    re.compile(r"^[一二三四五六七八九十]+[、.]\s*.+$"),
    re.compile(r"^（[一二三四五六七八九十]+）\s*.+$"),
    re.compile(r"^\d+[.、]\s*.+$"),
]


def is_heading(line: str) -> bool:
    return any(pattern.match(line.strip()) for pattern in HEADING_PATTERNS)


def build_chunks(pages: list[PageText], target_size: int = 900, overlap: int = 120) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    section = "未识别章节"
    buffer: list[tuple[int, str]] = []

    def flush() -> None:
        nonlocal buffer
        if not buffer:
            return
        text = "\n".join(item[1] for item in buffer).strip()
        if not text:
            buffer = []
            return
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"chunk-{len(chunks) + 1:04d}",
                page_start=buffer[0][0],
                page_end=buffer[-1][0],
                section_path=section,
                text=text,
            )
        )
        if overlap > 0 and len(text) > overlap:
            tail = text[-overlap:]
            buffer = [(buffer[-1][0], tail)]
        else:
            buffer = []

    for page in pages:
        for line in page.text.splitlines():
            clean = line.strip()
            if not clean:
                continue
            if is_heading(clean):
                if sum(len(item[1]) for item in buffer) >= 200:
                    flush()
                section = clean
            buffer.append((page.page, clean))
            if sum(len(item[1]) for item in buffer) >= target_size:
                flush()
    if buffer:
        flush()
    return chunks

