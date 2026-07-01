from src.chunker import build_chunks
from src.pdf_loader import PageText


def test_build_chunks_keeps_page_numbers():
    pages = [
        PageText(page=1, text="一、标题\n" + "实践和认识。" * 120),
        PageText(page=2, text="二、标题\n" + "矛盾和发展。" * 120),
    ]
    chunks = build_chunks(pages, target_size=200, overlap=20)
    assert chunks
    assert chunks[0].page_start == 1
    assert chunks[-1].page_end in {1, 2}

