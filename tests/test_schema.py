from src.schemas import QuestionSet


def test_question_schema_accepts_sample():
    data = {
        "questions": [
            {
                "question_type": "单项选择题",
                "stem": "实践的观点在认识论中是（　　）",
                "options": {"A": "首要观点", "B": "次要观点", "C": "无关观点", "D": "形式观点"},
                "answer": "A",
                "analysis": "实践是认识的基础。",
                "knowledge_point": "实践与认识",
                "chapter": "实践与认识",
                "source_pages": [12],
                "source_quote": "实践是认识的基础",
                "intent": "考查实践观点",
                "difficulty": "中等",
            }
        ]
    }
    question_set = QuestionSet.model_validate(data)
    assert question_set.questions[0].answer_text() == "A"


def test_question_schema_normalizes_model_sub_question_objects():
    data = {
        "questions": [
            {
                "question_type": "材料分析题",
                "stem": "阅读材料并回答问题。",
                "answer": {"analysis": "参考答案要点。"},
                "analysis": "参考答案要点。",
                "knowledge_point": "马克思主义基本特征",
                "chapter": "导论",
                "source_pages": "1-2",
                "source_quote": "马克思主义具有鲜明的实践品格",
                "intent": "考查材料分析能力",
                "difficulty": "中等",
                "material": "某同学围绕马克思主义基本特征展开讨论。",
                "sub_questions": [
                    {"stem": "马克思主义的基本特征有哪些？", "answer": "科学性、人民性、实践性和发展性。"},
                    {"stem": "认识过程体现了怎样的辩证关系？", "answer": "体现实践与认识的辩证关系。"},
                ],
            }
        ]
    }
    question_set = QuestionSet.model_validate(data)
    question = question_set.questions[0]
    assert question.sub_questions == ["马克思主义的基本特征有哪些？", "认识过程体现了怎样的辩证关系？"]
    assert question.source_pages == [1, 2]
    assert question.answer_text() == "参考答案要点。"
