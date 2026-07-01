from pathlib import Path

from src.file_resolver import MD_BACK_NAME, MD_FRONT_NAME
from src.md_exam_loader import MarkdownExamLoader


def test_parse_front_bank_counts():
    bank = MarkdownExamLoader().load(Path.cwd() / MD_FRONT_NAME)
    assert bank.counts == {
        "单项选择题": 40,
        "多项选择题": 20,
        "辨析题": 10,
        "简答题": 14,
        "论述题": 4,
        "材料分析题": 3,
    }
    assert bank.answers_found


def test_parse_back_bank_counts():
    bank = MarkdownExamLoader().load(Path.cwd() / MD_BACK_NAME)
    assert bank.counts == {
        "单项选择题": 45,
        "多项选择题": 20,
        "辨析题": 10,
        "简答题": 15,
        "论述题": 4,
        "材料分析题": 3,
    }


def test_parse_answers_and_materials():
    bank = MarkdownExamLoader().load(Path.cwd() / MD_FRONT_NAME)
    first_choice = next(item for item in bank.examples if item.question_type == "单项选择题")
    assert first_choice.answer == "A"
    assert first_choice.options["A"]
    materials = [item for item in bank.examples if item.question_type == "材料分析题"]
    assert len(materials) >= 1
    assert len(materials[0].sub_questions) >= 2

