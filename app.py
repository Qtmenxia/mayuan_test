from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.chunker import build_chunks
from src.config import Settings, normalize_openrouter_model
from src.exam_profiles import CONFUSING_PAIRS, QUESTION_TYPE_PRESETS
from src.exporter import export_csv, export_exam_bank_markdown, export_json
from src.file_resolver import inspect_sources, resolve_all_sources
from src.generator import QuestionGenerator
from src.md_exam_loader import MarkdownExamLoader, QUESTION_TYPES
from src.openrouter_client import OpenRouterClient
from src.pdf_loader import PDFLoader
from src.retriever import BM25Retriever
from src.schemas import GenerationConfig, QuestionSet
from src.style_retriever import StyleRetriever


PROJECT_ROOT = Path(__file__).resolve().parent


st.set_page_config(page_title="马原智能出题器", page_icon="📚", layout="wide")


@st.cache_resource(show_spinner=False)
def load_resources(project_root: str):
    root = Path(project_root)
    sources = resolve_all_sources(root)
    pages = PDFLoader().load(sources["pdf"])
    chunks = build_chunks(pages)
    knowledge_retriever = BM25Retriever(chunks)
    banks = MarkdownExamLoader().load_many([sources["front_md"], sources["back_md"]])
    style_retriever = StyleRetriever(banks)
    return sources, pages, chunks, banks, knowledge_retriever, style_retriever


def sidebar_settings() -> Settings:
    base = Settings.from_env(PROJECT_ROOT)
    st.sidebar.header("OpenRouter")
    api_key = st.sidebar.text_input("API Key", value=base.openrouter_api_key, type="password")
    base_url = st.sidebar.text_input("Base URL", value=base.openrouter_base_url)
    model = st.sidebar.text_input("Model", value=base.openrouter_model)
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, min(max(base.temperature, 0.0), 1.0), 0.05)
    max_tokens = st.sidebar.number_input("Max tokens", min_value=512, max_value=64000, value=min(base.max_tokens, 64000), step=512)
    return Settings(
        openrouter_api_key=api_key,
        openrouter_base_url=base_url,
        openrouter_model=normalize_openrouter_model(model),
        openrouter_http_referer=base.openrouter_http_referer,
        openrouter_app_title=base.openrouter_app_title,
        temperature=temperature,
        max_tokens=int(max_tokens),
    )


def show_source_status() -> None:
    st.sidebar.header("资料文件")
    for status in inspect_sources(PROJECT_ROOT):
        if status.found:
            st.sidebar.success(f"{status.label}: 已找到")
            st.sidebar.caption(str(status.path))
        else:
            st.sidebar.error(f"{status.label}: 未找到")


def init_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_question_set", None)
    st.session_state.setdefault("last_warnings", [])


def make_generator(settings: Settings, knowledge_retriever, style_retriever) -> QuestionGenerator:
    return QuestionGenerator(knowledge_retriever, style_retriever, OpenRouterClient(settings))


def render_question_set(question_set: QuestionSet, warnings: list[str], key_prefix: str) -> None:
    md = export_exam_bank_markdown(question_set)
    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "Markdown",
        md,
        file_name="mayuan_exam_bank.md",
        mime="text/markdown",
        key=f"{key_prefix}-download-md",
    )
    col2.download_button(
        "JSON",
        export_json(question_set),
        file_name="mayuan_exam_bank.json",
        mime="application/json",
        key=f"{key_prefix}-download-json",
    )
    col3.download_button(
        "CSV",
        export_csv(question_set),
        file_name="mayuan_exam_bank.csv",
        mime="text/csv",
        key=f"{key_prefix}-download-csv",
    )
    if warnings:
        with st.expander("校验提示", expanded=True):
            for warning in warnings:
                st.warning(warning)
    tab_questions, tab_answers, tab_full = st.tabs(["题目版", "答案版", "完整 Markdown"])
    before_answers, _, after_answers = md.partition("# 参考答案")
    tab_questions.markdown(before_answers)
    tab_answers.markdown("# 参考答案" + after_answers if after_answers else "暂无答案")
    tab_full.code(md, language="markdown")


def generation_tab(settings: Settings, knowledge_retriever, style_retriever) -> None:
    profile_name = st.selectbox("模板", list(QUESTION_TYPE_PRESETS.keys()))
    profile = QUESTION_TYPE_PRESETS[profile_name]
    scope = st.text_input("范围", value=profile["scope"])
    page_range = st.text_input("页码范围", value=profile["page_range"])
    chapter = st.text_input("章节/主题", value="")
    difficulty = st.selectbox("难度", ["简单", "中等", "困难"], index=1)
    small_test = st.checkbox("小题量测试", value=True)
    defaults = profile["counts"].copy()
    if small_test:
        defaults = {"单项选择题": 5, "多项选择题": 3, "辨析题": 2, "简答题": 2, "论述题": 1, "材料分析题": 1}

    st.subheader("题量")
    cols = st.columns(6)
    counts = {}
    for col, question_type in zip(cols, QUESTION_TYPES):
        counts[question_type] = col.number_input(question_type, min_value=0, max_value=60, value=defaults.get(question_type, 0), step=1)

    if st.button("生成仿真题库", type="primary"):
        generator = make_generator(settings, knowledge_retriever, style_retriever)
        all_questions = []
        warnings: list[str] = []
        progress = st.progress(0)
        active_types = [(qt, count) for qt, count in counts.items() if count > 0]
        for index, (question_type, count) in enumerate(active_types, start=1):
            config = GenerationConfig(
                question_type=question_type,
                count=int(count),
                chapter=chapter,
                page_range=page_range,
                knowledge_point=scope,
                difficulty=difficulty,
                temperature=settings.temperature,
            )
            with st.spinner(f"生成 {question_type} ..."):
                result, result_warnings, _ = generator.generate_questions(config)
            all_questions.extend(result.questions)
            warnings.extend(result_warnings)
            progress.progress(index / max(len(active_types), 1))
        question_set = QuestionSet(scope=scope, questions=all_questions)
        st.session_state["last_question_set"] = question_set
        st.session_state["last_warnings"] = warnings
        st.session_state["history"].append(question_set)

    if st.session_state.get("last_question_set"):
        render_question_set(
            st.session_state["last_question_set"],
            st.session_state.get("last_warnings", []),
            "generation-last",
        )


def single_tab(settings: Settings, knowledge_retriever, style_retriever) -> None:
    col1, col2 = st.columns(2)
    question_type = col1.selectbox("题型", QUESTION_TYPES)
    difficulty = col2.selectbox("难度", ["简单", "中等", "困难"], index=1, key="single_difficulty")
    count = st.slider("数量", 1, 20, 5)
    chapter = st.text_input("章节", key="single_chapter")
    page_range = st.text_input("页码范围", key="single_page_range")
    knowledge_point = st.text_input("知识点", key="single_knowledge_point")
    if st.button("生成题目", type="primary"):
        config = GenerationConfig(
            question_type=question_type,
            count=count,
            chapter=chapter,
            page_range=page_range,
            knowledge_point=knowledge_point,
            difficulty=difficulty,
            temperature=settings.temperature,
        )
        generator = make_generator(settings, knowledge_retriever, style_retriever)
        result, warnings, _ = generator.generate_questions(config)
        st.session_state["last_question_set"] = result
        st.session_state["last_warnings"] = warnings
        st.session_state["history"].append(result)
    if st.session_state.get("last_question_set"):
        render_question_set(
            st.session_state["last_question_set"],
            st.session_state.get("last_warnings", []),
            "single-last",
        )


def confusing_tab(settings: Settings, knowledge_retriever, style_retriever) -> None:
    labels = [f"{left} / {right}" for left, right, _ in CONFUSING_PAIRS]
    selected = st.selectbox("易混概念", labels)
    pair = CONFUSING_PAIRS[labels.index(selected)]
    st.caption(pair[2])
    question_type = st.selectbox("专项题型", ["单项选择题", "多项选择题", "辨析题", "简答题"], key="confusing_type")
    count = st.slider("专项数量", 1, 12, 4)
    if st.button("生成专项训练", type="primary"):
        config = GenerationConfig(
            question_type=question_type,
            count=count,
            knowledge_point=f"{pair[0]} 与 {pair[1]}：{pair[2]}",
            difficulty="中等",
            temperature=settings.temperature,
        )
        generator = make_generator(settings, knowledge_retriever, style_retriever)
        result, warnings, _ = generator.generate_questions(config)
        st.session_state["last_question_set"] = result
        st.session_state["last_warnings"] = warnings
        st.session_state["history"].append(result)
    if st.session_state.get("last_question_set"):
        render_question_set(
            st.session_state["last_question_set"],
            st.session_state.get("last_warnings", []),
            "confusing-last",
        )


def sample_tab(banks) -> None:
    for bank in banks:
        with st.expander(bank.path.name, expanded=True):
            st.write(bank.title)
            st.caption(bank.scope)
            st.dataframe({"题型": list(bank.counts.keys()), "数量": list(bank.counts.values())}, use_container_width=True)
            st.write("答案区解析：", "成功" if bank.answers_found else "未识别")
            for example in bank.examples[:3]:
                st.markdown(f"**{example.question_type}**｜{example.stem}")


def search_tab(chunks, knowledge_retriever, style_retriever) -> None:
    query = st.text_input("检索关键词", value="矛盾的同一性和斗争性")
    if query:
        st.subheader("PDF 知识命中")
        for chunk, score in knowledge_retriever.search(query, top_k=5):
            with st.expander(f"第 {chunk.page_start}-{chunk.page_end} 页｜{chunk.section_path}｜{score:.3f}"):
                st.write(chunk.text)
        st.subheader("Markdown 风格命中")
        for example, score in style_retriever.search(query, top_k=5):
            st.markdown(f"**{example.source}｜{example.question_type}｜{score:.3f}**")
            st.write(example.stem)


def history_tab() -> None:
    history = st.session_state.get("history", [])
    if not history:
        st.info("暂无历史记录")
        return
    index = st.selectbox("记录", range(len(history)), format_func=lambda i: f"第 {i + 1} 次生成")
    render_question_set(history[index], [], f"history-{index}")
    if st.button("清空历史"):
        st.session_state["history"] = []
        st.rerun()


def main() -> None:
    init_state()
    st.title("马原智能出题器")
    settings = sidebar_settings()
    show_source_status()
    if st.sidebar.button("测试连接"):
        try:
            client = OpenRouterClient(settings)
            content = client.chat("只回复：连接成功", temperature=0, max_tokens=20)
            st.sidebar.success(content.strip()[:60])
        except Exception as exc:
            st.sidebar.error(str(exc))

    try:
        _, _, chunks, banks, knowledge_retriever, style_retriever = load_resources(str(PROJECT_ROOT))
    except Exception as exc:
        st.error(f"资料加载失败：{exc}")
        return

    tabs = st.tabs(["仿真题库生成", "单题/批量出题", "易混概念专项", "样例题库解析", "知识库检索", "历史记录/导出"])
    with tabs[0]:
        generation_tab(settings, knowledge_retriever, style_retriever)
    with tabs[1]:
        single_tab(settings, knowledge_retriever, style_retriever)
    with tabs[2]:
        confusing_tab(settings, knowledge_retriever, style_retriever)
    with tabs[3]:
        sample_tab(banks)
    with tabs[4]:
        search_tab(chunks, knowledge_retriever, style_retriever)
    with tabs[5]:
        history_tab()


if __name__ == "__main__":
    main()
