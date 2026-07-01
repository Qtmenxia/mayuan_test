from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PDF_NAME = "（修正两处错误）马原知识点总结（2026春季学期）.pdf"
MD_FRONT_NAME = "马原前16页应试题库.md"
MD_BACK_NAME = "马原17-31页应试题库.md"


@dataclass(frozen=True)
class SourceStatus:
    key: str
    label: str
    filename: str
    path: Path | None
    found: bool
    message: str


def resolve_data_file(filename: str, project_root: str | Path = ".") -> Path:
    root = Path(project_root).resolve()
    candidates = [root / filename, root / "data" / filename]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"未找到 {filename}。请把文件放到项目根目录或 data/ 目录。")


def try_resolve_data_file(filename: str, project_root: str | Path = ".") -> Path | None:
    try:
        return resolve_data_file(filename, project_root)
    except FileNotFoundError:
        return None


def resolve_all_sources(project_root: str | Path = ".") -> dict[str, Path]:
    return {
        "pdf": resolve_data_file(PDF_NAME, project_root),
        "front_md": resolve_data_file(MD_FRONT_NAME, project_root),
        "back_md": resolve_data_file(MD_BACK_NAME, project_root),
    }


def inspect_sources(project_root: str | Path = ".") -> list[SourceStatus]:
    specs = [
        ("pdf", "PDF 知识底稿", PDF_NAME),
        ("front_md", "前16页题库样例", MD_FRONT_NAME),
        ("back_md", "17-31页题库样例", MD_BACK_NAME),
    ]
    statuses: list[SourceStatus] = []
    for key, label, filename in specs:
        path = try_resolve_data_file(filename, project_root)
        statuses.append(
            SourceStatus(
                key=key,
                label=label,
                filename=filename,
                path=path,
                found=path is not None,
                message="已找到" if path else "未找到",
            )
        )
    return statuses

