from __future__ import annotations

import json
import re
from difflib import SequenceMatcher

from pydantic import ValidationError

from .schemas import GeneratedQuestion, QuestionSet


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.S)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def parse_question_set(raw: str, title: str = "马克思主义基本原理 应试题库（自动生成）", scope: str = "") -> QuestionSet:
    data = extract_json(raw)
    if isinstance(data, list):
        data = {"questions": data}
    if "questions" not in data and "题目" in data:
        data["questions"] = data["题目"]
    data.setdefault("title", title)
    data.setdefault("scope", scope)
    return QuestionSet.model_validate(data)


def too_similar(a: str, b: str, threshold: float = 0.86) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= threshold


def validate_question(question: GeneratedQuestion, style_stems: list[str] | None = None) -> list[str]:
    warnings: list[str] = []
    if question.question_type == "单项选择题":
        if set(question.options.keys()) != {"A", "B", "C", "D"}:
            warnings.append("单选题选项不是 A/B/C/D 四项。")
        if question.answer_text() not in {"A", "B", "C", "D"}:
            warnings.append("单选题答案不是单个 A/B/C/D。")
    if question.question_type == "多项选择题":
        answer = question.answer_text()
        if len(answer) < 2 or any(ch not in "ABCD" for ch in answer):
            warnings.append("多选题答案应至少包含两个 A/B/C/D 字母。")
    if question.question_type == "辨析题" and not question.answer_text().startswith(("正确", "错误", "不准确")):
        warnings.append("辨析题答案未以“正确/错误/不准确”开头。")
    if question.question_type == "材料分析题":
        if not question.material:
            warnings.append("材料分析题缺少 material。")
        if len(question.sub_questions) < 2:
            warnings.append("材料分析题 sub_questions 少于 2 个。")
    if not question.source_pages:
        warnings.append("缺少 source_pages。")
    if not question.source_quote:
        warnings.append("缺少 source_quote。")
    for stem in style_stems or []:
        if too_similar(question.stem, stem):
            warnings.append("题干与样例题库相似度过高。")
            break
    return warnings


def validate_raw_question_set(raw: str) -> tuple[QuestionSet | None, list[str]]:
    try:
        question_set = parse_question_set(raw)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        return None, [f"JSON 或结构校验失败：{exc}"]
    warnings: list[str] = []
    for index, question in enumerate(question_set.questions, start=1):
        for warning in validate_question(question):
            warnings.append(f"第 {index} 题：{warning}")
    return question_set, warnings

