from __future__ import annotations

import json

from .schemas import GenerationConfig


QUESTION_JSON_SCHEMA_HINT = {
    "questions": [
        {
            "question_type": "单项选择题",
            "stem": "题干",
            "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            "answer": "A",
            "analysis": "解析或要点",
            "knowledge_point": "知识点",
            "chapter": "章节",
            "source_pages": [1],
            "source_quote": "必须来自PDF片段的原文短句",
            "intent": "命题意图",
            "difficulty": "中等",
            "material": "",
            "sub_questions": [],
        }
    ]
}


def build_question_prompt(
    config: GenerationConfig,
    knowledge_context: str,
    style_summary: str,
    style_examples: str,
) -> str:
    schema = json.dumps(QUESTION_JSON_SCHEMA_HINT, ensure_ascii=False, indent=2)
    return f"""
你是本科《马克思主义基本原理》期末考试命题老师。请严格依据 PDF 知识片段生成题目。

硬性要求：
1. 严格依据 PDF，不得补充 PDF 片段之外的知识。
2. Markdown题库风格样例只用于模仿题型结构、题干语气、选项组织和答案写法，禁止照抄原题或答案。
3. 禁止照抄、改写过近或复用样例题干；同一知识点也要更换设问角度、材料或干扰项。
4. 输出 JSON，且只输出 JSON，不要 Markdown 代码块，不要解释性前后缀。
5. 每题必须包含答案、解析或要点、知识点、章节、source_pages、source_quote、命题意图。
6. 单选题必须有 A/B/C/D 四个选项且只有一个答案；多选题必须有 A/B/C/D 四个选项且至少两个答案。
7. 辨析题答案必须以“正确”“错误”或“不准确”之一开头。
8. 材料分析题必须包含 material 和至少 2 个 sub_questions。

生成配置：
- 题型：{config.question_type}
- 数量：{config.count}
- 章节：{config.chapter or "按检索结果自动匹配"}
- 页码范围：{config.page_range or "不限"}
- 知识点：{config.knowledge_point or "按检索结果自动匹配"}
- 难度：{config.difficulty}

PDF材料：
{knowledge_context}

题库风格摘要：
{style_summary}

相似风格样例：
{style_examples}

JSON Schema 示例：
{schema}
""".strip()

