from __future__ import annotations

import json
import re
from typing import Any
from typing import Literal

from pydantic import BaseModel, Field, field_validator


QuestionType = Literal["单项选择题", "多项选择题", "辨析题", "简答题", "论述题", "材料分析题"]
Difficulty = Literal["简单", "中等", "困难"]


def _stringify_model_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("stem", "question", "text", "content", "answer", "analysis"):
            item = value.get(key)
            if item:
                return _stringify_model_value(item)
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "；".join(_stringify_model_value(item) for item in value if item is not None)
    return str(value)


class GeneratedQuestion(BaseModel):
    question_type: QuestionType
    stem: str
    options: dict[str, str] = Field(default_factory=dict)
    answer: str | list[str]
    analysis: str = ""
    knowledge_point: str
    chapter: str = ""
    source_pages: list[int] = Field(default_factory=list)
    source_quote: str
    intent: str
    difficulty: Difficulty = "中等"
    material: str = ""
    sub_questions: list[str] = Field(default_factory=list)

    @field_validator("answer", mode="before")
    @classmethod
    def normalize_answer(cls, answer: Any) -> Any:
        if isinstance(answer, dict):
            return _stringify_model_value(answer)
        if isinstance(answer, list):
            return [_stringify_model_value(item) for item in answer]
        return answer

    @field_validator("options")
    @classmethod
    def validate_option_keys(cls, options: dict[str, str]) -> dict[str, str]:
        if options and set(options.keys()) != {"A", "B", "C", "D"}:
            raise ValueError("客观题必须包含 A/B/C/D 四个选项")
        return options

    @field_validator("source_pages", mode="before")
    @classmethod
    def normalize_source_pages(cls, source_pages: Any) -> list[int]:
        if source_pages is None or source_pages == "":
            return []
        if isinstance(source_pages, int):
            return [source_pages]
        if isinstance(source_pages, str):
            return [int(item) for item in re.findall(r"\d+", source_pages)]
        if isinstance(source_pages, list):
            pages: list[int] = []
            for item in source_pages:
                if isinstance(item, int):
                    pages.append(item)
                elif isinstance(item, str):
                    pages.extend(int(match) for match in re.findall(r"\d+", item))
            return pages
        return []

    @field_validator("sub_questions", mode="before")
    @classmethod
    def normalize_sub_questions(cls, sub_questions: Any) -> list[str]:
        if sub_questions is None or sub_questions == "":
            return []
        if isinstance(sub_questions, str):
            return [sub_questions]
        if isinstance(sub_questions, list):
            return [_stringify_model_value(item) for item in sub_questions if _stringify_model_value(item)]
        if isinstance(sub_questions, dict):
            return [_stringify_model_value(sub_questions)]
        return [str(sub_questions)]

    def answer_text(self) -> str:
        if isinstance(self.answer, list):
            return "".join(self.answer)
        return str(self.answer)


class QuestionSet(BaseModel):
    title: str = "马克思主义基本原理 应试题库（自动生成）"
    scope: str = ""
    questions: list[GeneratedQuestion]


class GenerationConfig(BaseModel):
    question_type: QuestionType
    count: int = 5
    chapter: str = ""
    page_range: str = ""
    knowledge_point: str = ""
    difficulty: Difficulty = "中等"
    style_profile: str = "自动匹配"
    knowledge_top_k: int = 6
    style_top_k: int = 5
    temperature: float = 0.35
