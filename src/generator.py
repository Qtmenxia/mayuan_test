from __future__ import annotations

from .prompts import build_question_prompt
from .schemas import GenerationConfig, QuestionSet
from .validator import parse_question_set, validate_question


class QuestionGenerator:
    def __init__(self, knowledge_retriever, style_retriever, llm_client):
        self.knowledge_retriever = knowledge_retriever
        self.style_retriever = style_retriever
        self.llm = llm_client

    def generate_questions(self, config: GenerationConfig) -> tuple[QuestionSet, list[str], str]:
        knowledge_hits = self.knowledge_retriever.search(self._build_knowledge_query(config), top_k=config.knowledge_top_k)
        style_hits = self.style_retriever.search(
            self._build_style_query(config),
            question_type=config.question_type,
            top_k=config.style_top_k,
        )
        knowledge_context = self._format_knowledge_context(knowledge_hits)
        style_examples = self._format_style_examples(style_hits)
        prompt = build_question_prompt(config, knowledge_context, self._style_summary(style_hits), style_examples)
        raw = self.llm.chat(prompt, temperature=config.temperature)
        question_set = parse_question_set(
            raw,
            scope="；".join(part for part in [config.chapter, config.page_range, config.knowledge_point] if part),
        )
        self._apply_source_fallbacks(question_set, knowledge_hits)
        style_stems = [hit[0].stem for hit in style_hits]
        warnings = []
        for index, question in enumerate(question_set.questions, start=1):
            for warning in validate_question(question, style_stems):
                warnings.append(f"第 {index} 题：{warning}")
        return question_set, warnings, raw

    def _apply_source_fallbacks(self, question_set: QuestionSet, knowledge_hits) -> None:
        fallback_hit = knowledge_hits[0][0] if knowledge_hits else None
        for question in question_set.questions:
            if question.source_pages and question.source_quote:
                continue
            query = " ".join(
                part
                for part in [question.knowledge_point, question.chapter, question.stem]
                if part
            )
            hits = self.knowledge_retriever.search(query, top_k=1) if query else []
            chunk = hits[0][0] if hits else fallback_hit
            if not chunk:
                continue
            if not question.source_pages:
                question.source_pages = list(range(chunk.page_start, chunk.page_end + 1))
            if not question.source_quote:
                question.source_quote = self._short_source_quote(chunk.text)

    def _short_source_quote(self, text: str, limit: int = 90) -> str:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line:
                return line[:limit]
        return text.strip()[:limit]

    def _build_knowledge_query(self, config: GenerationConfig) -> str:
        return " ".join(
            part
            for part in [config.chapter, config.page_range, config.knowledge_point, config.question_type, config.difficulty]
            if part
        )

    def _build_style_query(self, config: GenerationConfig) -> str:
        return " ".join(
            part
            for part in [config.question_type, config.knowledge_point, config.chapter, "本科马原期末 应试题库"]
            if part
        )

    def _format_knowledge_context(self, hits) -> str:
        parts = []
        for chunk, score in hits:
            pages = f"第{chunk.page_start}页" if chunk.page_start == chunk.page_end else f"第{chunk.page_start}-{chunk.page_end}页"
            parts.append(f"[{pages}｜{chunk.section_path}｜score={score:.3f}]\n{chunk.text}")
        return "\n\n".join(parts)

    def _format_style_examples(self, hits) -> str:
        parts = []
        for example, score in hits:
            options = "\n".join(f"{key}. {value}" for key, value in example.options.items())
            parts.append(
                f"[{example.source}｜{example.question_type}｜score={score:.3f}]\n"
                f"题干：{example.stem}\n{options}\n答案样式：{example.answer or example.answer_excerpt[:160]}"
            )
        return "\n\n".join(parts)

    def _style_summary(self, hits) -> str:
        if not hits:
            return "当前缺少风格样例，只能依据PDF生成，无法进入高仿题库模式。"
        types = sorted({hit[0].question_type for hit in hits})
        return "样例题库采用先题目后参考答案结构，客观题 A/B/C/D 排列，主观题以要点式答案组织；命中题型：" + "、".join(types)
