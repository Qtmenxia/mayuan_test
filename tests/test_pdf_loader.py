from pathlib import Path

import pytest

from src.file_resolver import PDF_NAME
from src.pdf_loader import PDFLoader


def test_pdf_loader_reads_pages():
    try:
        pages = PDFLoader().load(Path.cwd() / PDF_NAME)
    except RuntimeError as exc:
        pytest.skip(str(exc))
    assert len(pages) > 20
    text = "\n".join(page.text for page in pages)
    assert "马克思主义" in text
    assert "矛盾的同一性" in text

