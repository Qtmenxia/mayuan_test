from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PageText:
    page: int
    text: str


class PDFLoader:
    def load(self, pdf_path: str | Path) -> list[PageText]:
        try:
            import fitz
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("缺少 pymupdf，请先安装 requirements.txt 中的依赖。") from exc

        doc = fitz.open(str(pdf_path))
        pages: list[PageText] = []
        try:
            for index, page in enumerate(doc, start=1):
                text = self._clean(page.get_text("text"))
                pages.append(PageText(page=index, text=text))
        finally:
            doc.close()
        return pages

    def _clean(self, text: str) -> str:
        lines: list[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.isdigit():
                continue
            if line in {"马克思主义基本原理知识点梳理", "马原知识点总结"}:
                continue
            lines.append(line)
        return "\n".join(lines)

