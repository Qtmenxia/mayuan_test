from __future__ import annotations

import csv
import io
import json
from collections import defaultdict

from .md_exam_loader import QUESTION_TYPES
from .schemas import GeneratedQuestion, QuestionSet


HEADINGS = {
    "单项选择题": "一、单项选择题",
    "多项选择题": "二、多项选择题",
    "辨析题": "三、辨析题（判断正误并说明理由）",
    "简答题": "四、简答题",
    "论述题": "五、论述题",
    "材料分析题": "六、材料分析题",
}


def group_questions(question_set: QuestionSet) -> dict[str, list[GeneratedQuestion]]:
    grouped: dict[str, list[GeneratedQuestion]] = defaultdict(list)
    for question in question_set.questions:
        grouped[question.question_type].append(question)
    return grouped


def format_objective_answer_key(questions: list[GeneratedQuestion]) -> str:
    parts = []
    for index, question in enumerate(questions, start=1):
        parts.append(f"{index}.{question.answer_text()}")
    lines = ["　".join(parts[index : index + 10]) for index in range(0, len(parts), 10)]
    return "\n".join(lines)


def _render_question(index: int, question: GeneratedQuestion) -> str:
    if question.question_type in {"单项选择题", "多项选择题"}:
        options = "\n".join(f"   {key}. {value}" for key, value in question.options.items())
        return f"{index}. {question.stem}\n{options}"
    if question.question_type == "材料分析题":
        sub = "\n".join(f"（{sub_index}）{text}" for sub_index, text in enumerate(question.sub_questions, start=1))
        return f"**材料{index}**\n{question.material}\n\n**问题：**\n{sub}"
    return f"{index}. {question.stem}"


def _render_subjective_answers(questions: list[GeneratedQuestion]) -> str:
    parts: list[str] = []
    for index, question in enumerate(questions, start=1):
        if question.question_type == "材料分析题":
            parts.append(f"**材料{index}答案要点**\n{question.analysis or question.answer_text()}")
        elif question.question_type == "辨析题":
            parts.append(f"{index}. **{question.answer_text()}。** {question.analysis}")
        else:
            parts.append(f"**{index}. {question.knowledge_point}**\n{question.analysis or question.answer_text()}")
    return "\n\n".join(parts)


def export_exam_bank_markdown(question_set: QuestionSet) -> str:
    grouped = group_questions(question_set)
    lines = [
        f"# {question_set.title}",
        "",
        f"> 范围：{question_set.scope or '按用户配置与PDF检索结果生成'}",
        "> 题型贴合本科马原期末出题习惯：单选、多选、辨析、简答、论述、材料分析。答案附在每部分末尾。",
        "",
        "---",
        "",
    ]
    for question_type in QUESTION_TYPES:
        questions = grouped.get(question_type, [])
        if not questions:
            continue
        lines.append(f"## {HEADINGS[question_type]}")
        lines.append("")
        for index, question in enumerate(questions, start=1):
            lines.append(_render_question(index, question))
            lines.append("")

    lines.extend(["---", "---", "", "# 参考答案", ""])
    for question_type in QUESTION_TYPES:
        questions = grouped.get(question_type, [])
        if not questions:
            continue
        suffix = "（要点）" if question_type in {"辨析题", "简答题", "论述题", "材料分析题"} else ""
        lines.append(f"## {HEADINGS[question_type]}{suffix}")
        lines.append("")
        if question_type in {"单项选择题", "多项选择题"}:
            lines.append(format_objective_answer_key(questions))
        else:
            lines.append(_render_subjective_answers(questions))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def export_json(question_set: QuestionSet) -> str:
    return question_set.model_dump_json(indent=2)


def export_csv(question_set: QuestionSet) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "question_type",
            "stem",
            "answer",
            "analysis",
            "knowledge_point",
            "chapter",
            "source_pages",
            "source_quote",
            "intent",
            "difficulty",
        ],
    )
    writer.writeheader()
    for question in question_set.questions:
        row = question.model_dump()
        row["answer"] = question.answer_text()
        row["source_pages"] = ",".join(str(page) for page in question.source_pages)
        writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
    return output.getvalue()

