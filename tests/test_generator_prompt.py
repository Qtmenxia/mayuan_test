from src.prompts import build_question_prompt
from src.schemas import GenerationConfig


def test_prompt_contains_required_constraints():
    prompt = build_question_prompt(
        GenerationConfig(question_type="单项选择题", count=2),
        knowledge_context="PDF片段",
        style_summary="样例摘要",
        style_examples="样例题",
    )
    assert "严格依据 PDF" in prompt
    assert "Markdown题库风格样例只用于模仿" in prompt
    assert "禁止照抄" in prompt
    assert "输出 JSON" in prompt
