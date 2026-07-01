from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


QUESTION_TYPES = [
    "单项选择题",
    "多项选择题",
    "辨析题",
    "简答题",
    "论述题",
    "材料分析题",
]


@dataclass
class StyleExample:
    source: str
    question_type: str
    stem: str
    options: dict[str, str] = field(default_factory=dict)
    answer: str = ""
    answer_excerpt: str = ""
    material: str = ""
    sub_questions: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        option_text = " ".join(f"{key}.{value}" for key, value in self.options.items())
        return " ".join([self.question_type, self.stem, option_text, self.answer_excerpt]).strip()


@dataclass
class ExamBank:
    path: Path
    title: str
    scope: str
    counts: dict[str, int]
    examples: list[StyleExample]
    answers_found: bool


def _normalize_heading(text: str) -> str | None:
    for question_type in QUESTION_TYPES:
        if question_type in text:
            return question_type
    return None


def _section_map(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s*[一二三四五六]、(.+?)\s*$", text, flags=re.M))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        question_type = _normalize_heading(match.group(1))
        if not question_type:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[question_type] = text[start:end].strip()
    return sections


def _split_question_blocks(section_text: str) -> list[str]:
    starts = list(re.finditer(r"(?m)^\s*\d+\.\s+", section_text))
    blocks: list[str] = []
    for index, match in enumerate(starts):
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(section_text)
        block = section_text[start:end].strip()
        if block:
            blocks.append(block)
    return blocks


def _parse_choice_block(block: str) -> tuple[str, dict[str, str]]:
    lines = block.splitlines()
    stem_parts: list[str] = []
    options: dict[str, str] = {}
    for line in lines:
        option_match = re.match(r"^\s*([A-D])\.\s*(.+?)\s*$", line)
        if option_match:
            options[option_match.group(1)] = option_match.group(2).strip()
        elif not options:
            stem_parts.append(line.strip())
    stem = " ".join(stem_parts)
    stem = re.sub(r"^\d+\.\s*", "", stem).strip()
    return stem, options


def _parse_material_blocks(section_text: str, source: str, answer_sections: dict[str, str]) -> list[StyleExample]:
    starts = list(re.finditer(r"(?m)^\*\*材料[一二三四五六七八九十\d]+.*?\*\*\s*$", section_text))
    examples: list[StyleExample] = []
    if not starts:
        return examples
    for index, match in enumerate(starts):
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(section_text)
        block = section_text[start:end].strip()
        material_part, _, question_part = block.partition("**问题：**")
        material = re.sub(r"^\*\*材料.*?\*\*", "", material_part, flags=re.S).strip()
        sub_questions = [
            item.strip()
            for item in re.findall(r"（\d+）(.+?)(?=(?:\n?（\d+）)|$)", question_part, flags=re.S)
            if item.strip()
        ]
        examples.append(
            StyleExample(
                source=source,
                question_type="材料分析题",
                stem="；".join(sub_questions) or "材料分析",
                material=material,
                sub_questions=sub_questions,
                answer_excerpt=answer_sections.get("材料分析题", "")[:500],
            )
        )
    return examples


def _objective_answers(answer_text: str) -> dict[int, str]:
    return {int(num): ans for num, ans in re.findall(r"(\d+)\.([A-D]+)", answer_text)}


class MarkdownExamLoader:
    def load(self, path: str | Path) -> ExamBank:
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", text, flags=re.M)
        title = title_match.group(1).strip() if title_match else path.stem
        scope_match = re.search(r"^>\s*范围：(.+?)(?=\n>)", text, flags=re.M | re.S)
        scope = scope_match.group(1).strip().replace("\n", " ") if scope_match else ""

        questions_text, sep, answers_text = text.partition("# 参考答案")
        question_sections = _section_map(questions_text)
        answer_sections = _section_map(answers_text)
        examples: list[StyleExample] = []

        for question_type, section_text in question_sections.items():
            if question_type in {"单项选择题", "多项选择题"}:
                answers = _objective_answers(answer_sections.get(question_type, ""))
                for index, block in enumerate(_split_question_blocks(section_text), start=1):
                    stem, options = _parse_choice_block(block)
                    examples.append(
                        StyleExample(
                            source=path.name,
                            question_type=question_type,
                            stem=stem,
                            options=options,
                            answer=answers.get(index, ""),
                        )
                    )
            elif question_type == "材料分析题":
                examples.extend(_parse_material_blocks(section_text, path.name, answer_sections))
            else:
                answer_excerpt = answer_sections.get(question_type, "")[:500]
                for block in _split_question_blocks(section_text):
                    stem = re.sub(r"^\d+\.\s*", "", block.splitlines()[0]).strip()
                    examples.append(
                        StyleExample(
                            source=path.name,
                            question_type=question_type,
                            stem=stem,
                            answer_excerpt=answer_excerpt,
                        )
                    )

        counts = {question_type: 0 for question_type in QUESTION_TYPES}
        for example in examples:
            counts[example.question_type] += 1
        return ExamBank(path=path, title=title, scope=scope, counts=counts, examples=examples, answers_found=bool(sep))

    def load_many(self, paths: list[str | Path]) -> list[ExamBank]:
        return [self.load(path) for path in paths if Path(path).exists()]

