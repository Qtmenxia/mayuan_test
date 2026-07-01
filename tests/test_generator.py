from src.chunker import KnowledgeChunk
from src.generator import QuestionGenerator
from src.schemas import GenerationConfig


class FakeRetriever:
    def __init__(self):
        self.chunk = KnowledgeChunk(
            chunk_id="c1",
            page_start=3,
            page_end=4,
            section_path="测试章节",
            text="实践是认识的基础。\n认识来源于实践并反作用于实践。",
        )

    def search(self, query, top_k=1, **kwargs):
        return [(self.chunk, 1.0)]


class FakeStyleRetriever:
    def search(self, query, question_type=None, top_k=5):
        return []


class FakeLLM:
    def chat(self, messages, temperature=None, max_tokens=None):
        return """
        {
          "questions": [
            {
              "question_type": "单项选择题",
              "stem": "实践在认识论中的地位是（　　）",
              "options": {"A": "基础", "B": "形式", "C": "结果", "D": "目的之外的环节"},
              "answer": "A",
              "analysis": "实践是认识的基础。",
              "knowledge_point": "实践与认识",
              "chapter": "实践与认识",
              "source_pages": [],
              "source_quote": "",
              "intent": "考查实践观点",
              "difficulty": "中等"
            }
          ]
        }
        """


def test_generator_fills_missing_source_fields():
    generator = QuestionGenerator(FakeRetriever(), FakeStyleRetriever(), FakeLLM())
    question_set, warnings, _ = generator.generate_questions(
        GenerationConfig(question_type="单项选择题", count=1, knowledge_point="实践与认识")
    )
    question = question_set.questions[0]
    assert question.source_pages == [3, 4]
    assert question.source_quote == "实践是认识的基础。"
    assert not any("source_pages" in warning or "source_quote" in warning for warning in warnings)
