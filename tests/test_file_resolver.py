from pathlib import Path

import pytest

from src.file_resolver import MD_FRONT_NAME, resolve_data_file


def test_resolve_root_file():
    path = resolve_data_file(MD_FRONT_NAME, Path.cwd())
    assert path.name == MD_FRONT_NAME


def test_resolve_data_file(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    target = data / "demo.txt"
    target.write_text("ok", encoding="utf-8")
    assert resolve_data_file("demo.txt", tmp_path) == target.resolve()


def test_resolve_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="项目根目录或 data"):
        resolve_data_file("missing.txt", tmp_path)

