# 马原智能出题器开发任务书（Codex 实施版｜题库风格模拟增强版）

> 本版修改重点：项目根目录已经存在 3 个核心资料文件：
>
> 1. `（修正两处错误）马原知识点总结（2026春季学期）.pdf`：作为**知识依据**与页码来源；
> 2. `马原前16页应试题库.md`：作为**前半部分应试题库风格样例**；
> 3. `马原17-31页应试题库.md`：作为**后半部分应试题库风格样例**。
>
> 出题器必须做到：**以 PDF 为知识底稿，以两个 Markdown 题库为命题风格、题型结构、答案组织方式和应试表达模板**。生成题目时不能简单复读样例题，也不能只让大模型自由发挥，而要“按 PDF 找依据、按两个 MD 仿格式、按本科马原期末习惯出题”。

---

## 1. 给 Codex 的总指令

你需要在当前仓库中实现一个本地运行的 Python Web 应用，优先采用 **Streamlit + 本地 RAG + OpenRouter Chat Completions** 的轻量架构。

系统目标不是做一个泛化的政治理论问答器，而是做一个**马原应试题库生成器**：

- 知识范围来自 PDF；
- 命题形式模拟两个 `.md` 题库；
- 输出风格贴近本科《马克思主义基本原理》期末考试；
- 前端便于交互，用户可以选择章节、页码范围、题型、数量、难度、仿真模板和导出格式。

必须完成：

1. 自动识别并读取项目根目录或 `data/` 目录中的 3 个资料文件。
2. 解析 PDF，建立带页码的知识库。
3. 解析两个 Markdown 题库，抽取题型结构、题干风格、选项风格、答案格式、材料分析格式，建立“风格样例库”。
4. 使用 OpenRouter API 调用大模型生成题目。
5. 前端支持 OpenRouter 配置、本地文件状态检查、题型/章节/页码/难度/数量配置、仿样例题库生成、预览、校验、导出。
6. 默认题型应优先模拟两个 `.md` 题库中的六类：**单项选择题、多项选择题、辨析题、简答题、论述题、材料分析题**。
7. 题目必须附答案、解析或要点、知识点、章节、来源页码、命题意图；整套题库导出时必须按两个 `.md` 的结构先列题目、后列参考答案。
8. 支持导出 Markdown、JSON、CSV；其中 Markdown 是主格式，必须尽量接近两个样例题库。
9. 提供 README、conda 环境文件、`.env.example`、基础测试脚本。

---

## 2. 资料文件与角色分工

### 2.1 文件放置约定

用户说明项目根目录已经存在两个 `.md` 文件以及 PDF。第一版程序必须支持以下两种放置方式：

```text
项目根目录/
├── app.py
├── （修正两处错误）马原知识点总结（2026春季学期）.pdf
├── 马原前16页应试题库.md
└── 马原17-31页应试题库.md
```

也支持更规范的：

```text
项目根目录/
├── app.py
└── data/
    ├── （修正两处错误）马原知识点总结（2026春季学期）.pdf
    ├── 马原前16页应试题库.md
    └── 马原17-31页应试题库.md
```

实现时写一个 `resolve_data_file()`，优先查根目录，再查 `data/`。

### 2.2 三类资料的职责

| 文件 | 用途 | 不能做什么 |
|---|---|---|
| PDF 知识点总结 | 作为题目知识依据、页码来源、source_quote 来源 | 不能只靠模型记忆补充 PDF 外知识 |
| `马原前16页应试题库.md` | 模拟前 16 页范围内的题库结构、题型、答案写法 | 不能逐题照抄生成重复题 |
| `马原17-31页应试题库.md` | 模拟第 17–31 页范围内的题库结构、题型、答案写法 | 不能逐题照抄生成重复题 |

### 2.3 已知样例题库结构

两个 `.md` 题库都采用相同的应试题库结构：

```text
# 马克思主义基本原理 应试题库（范围说明）

> 范围：……
> 题型贴合本科马原期末出题习惯：单选、多选、辨析、简答、论述、材料分析。答案附在每部分末尾。

---

## 一、单项选择题
## 二、多项选择题
## 三、辨析题
## 四、简答题
## 五、论述题
## 六、材料分析题

---
---

# 参考答案

## 一、单项选择题
## 二、多项选择题
## 三、辨析题（要点）
## 四、简答题（要点）
## 五、论述题（要点）
## 六、材料分析题（要点）
```

两个样例的题量特征：

| 样例文件 | 单选 | 多选 | 辨析 | 简答 | 论述 | 材料分析 |
|---|---:|---:|---:|---:|---:|---:|
| `马原前16页应试题库.md` | 40 | 20 | 10 | 14 | 4 | 3 |
| `马原17-31页应试题库.md` | 45 | 20 | 10 | 15 | 4 | 3 |

第一版可提供三个内置模板：

1. **前16页仿真题库**：默认题量 `40/20/10/14/4/3`；
2. **17-31页仿真题库**：默认题量 `45/20/10/15/4/3`；
3. **自定义小题库**：用户自行设置题量，但输出格式仍模拟两个 `.md`。

---

## 3. 本科马原题库风格模拟要求

### 3.1 题型模拟规则

默认不要再把“判断题、填空题、名词解释”作为主入口。除非用户明确开启扩展题型，否则主界面应优先展示两个 `.md` 样例中出现的六类题型。

| 题型 | 样例格式 | 生成要求 |
|---|---|---|
| 单项选择题 | `1. 题干是（　　）` + A/B/C/D | 4 个选项，只有 1 个正确答案；干扰项要来自相近概念或常见错误表述 |
| 多项选择题 | `1. ……包括（　　）` + A/B/C/D | 至少 2 个正确答案；答案形如 `ABCD`、`ABC`；解析要能说明为什么多选 |
| 辨析题 | `1. 某个判断句。` | 参考答案以 `**错误。**`、`**正确。**`、`**不准确。**` 开头，然后说明理由 |
| 简答题 | `1. 简述……。` | 答案按概念、关系、方法论或要点编号组织，长度适中 |
| 论述题 | `1. 试述……，并说明……。` | 答案比简答更综合，通常包含“原理 + 意义/现实联系” |
| 材料分析题 | `**材料一**` + 材料 + `**问题：**` | 材料 120-250 字；通常设置 2 个小问，答案分点 |

### 3.2 语言风格模拟规则

生成题目时要模仿样例题库的以下表达习惯：

1. 选择题题干多使用“是指”“决定了”“关系是”“根本标准是”“表现为”“不包括”等考试化表述。
2. 单选题选项中常设置“一项正确、三项混淆”的结构，错误项常见类型包括：
   - 把相对说成绝对；
   - 把条件性说成无条件；
   - 把决定作用和反作用颠倒；
   - 把根本动力、直接动力、重要动力混淆；
   - 把概念的自然属性和社会属性混淆。
3. 多选题多考“包括”“表现为”“关系是”“作用有”“条件有”。
4. 辨析题题干要像学生常犯错误，例如：
   - “新出现的事物就是新事物。”
   - “有用即真理。”
   - “科学技术是社会发展的根本动力。”
5. 简答题多用“简述……辩证关系及其方法论意义”“为什么说……”“简述……内容、表现形式和作用”。
6. 论述题多用“试述……原理，并联系实际说明……意义”。
7. 材料分析题要用现实或课堂常见材料引出原理，但答案所用原理必须来自 PDF。

### 3.3 严禁事项

1. 禁止逐题照抄两个样例 `.md` 中的原题。
2. 禁止把样例答案原封不动搬运成新题答案。
3. 禁止使用 PDF 中没有支撑的知识点。
4. 禁止输出“作为 AI”“根据常识”“我认为”等非考试语言。
5. 禁止把客观题答案写成模糊表达，例如“可能是 B”。
6. 禁止材料分析题只有材料没有问题，或只有答案没有评分要点。

---

## 4. 推荐技术架构

采用单机本地架构：

```text
用户浏览器
   │
   ▼
Streamlit 前端 app.py
   │
   ├── 配置管理：OpenRouter API Key / Base URL / Model
   ├── 文件发现：根目录与 data/ 双路径查找
   ├── PDF 解析：PyMuPDF，建立知识依据库
   ├── Markdown 题库解析：抽取样例题型、题干、选项、答案、材料格式
   ├── 检索：PDF 知识 BM25 + 样例风格 BM25
   ├── 出题引擎：Prompt 模板 + OpenRouter LLM
   ├── 校验器：JSON Schema / Markdown 结构校验 / 重复题检测
   └── 导出器：Markdown / JSON / CSV
```

第一版仍优先使用 **Streamlit**，不要复杂前后端分离。检索第一版用 **BM25 + jieba**，不要强依赖本地向量模型。

---

## 5. 目录结构

请 Codex 按以下结构创建项目。注意：资料文件允许在根目录或 `data/`，程序必须兼容。

```text
mayuan-question-generator/
├── app.py
├── README.md
├── environment.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── （修正两处错误）马原知识点总结（2026春季学期）.pdf      # 允许根目录
├── 马原前16页应试题库.md                                  # 允许根目录
├── 马原17-31页应试题库.md                                  # 允许根目录
├── data/                                                    # 可选规范目录
│   ├── （修正两处错误）马原知识点总结（2026春季学期）.pdf
│   ├── 马原前16页应试题库.md
│   └── 马原17-31页应试题库.md
├── outputs/
│   ├── papers/
│   ├── questions/
│   └── logs/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── file_resolver.py
│   ├── pdf_loader.py
│   ├── md_exam_loader.py
│   ├── chunker.py
│   ├── retriever.py
│   ├── style_retriever.py
│   ├── openrouter_client.py
│   ├── prompts.py
│   ├── schemas.py
│   ├── generator.py
│   ├── validator.py
│   ├── exporter.py
│   └── exam_profiles.py
└── tests/
    ├── test_file_resolver.py
    ├── test_pdf_loader.py
    ├── test_md_exam_loader.py
    ├── test_chunker.py
    ├── test_schema.py
    └── test_generator_prompt.py
```

---

## 6. Conda 环境配置

创建 `environment.yml`：

```yaml
name: mayuan-qgen
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pip
  - pip:
      - streamlit>=1.36.0
      - pymupdf>=1.24.0
      - python-dotenv>=1.0.1
      - openai>=1.40.0
      - pydantic>=2.7.0
      - pandas>=2.2.0
      - numpy>=1.26.0
      - scikit-learn>=1.5.0
      - rank-bm25>=0.2.2
      - jieba>=0.42.1
      - markdown>=3.6
      - pytest>=8.0.0
```

安装与启动：

```bash
conda env create -f environment.yml
conda activate mayuan-qgen
streamlit run app.py
```

---

## 7. OpenRouter API 配置

### 7.1 `.env.example`

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=~openai/gpt-latest
OPENROUTER_HTTP_REFERER=http://localhost:8501
OPENROUTER_APP_TITLE=Mayuan Question Generator
```

### 7.2 `src/openrouter_client.py`

```python
from openai import OpenAI
from .config import Settings

class OpenRouterClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            default_headers={
                "HTTP-Referer": settings.openrouter_http_referer or "http://localhost:8501",
                "X-OpenRouter-Title": settings.openrouter_app_title or "Mayuan Question Generator",
            },
        )

    def chat(self, messages, temperature=0.3, max_tokens=4096):
        if not self.settings.openrouter_api_key:
            raise RuntimeError("未配置 OPENROUTER_API_KEY。请在侧边栏或 .env 中填写。")
        resp = self.client.chat.completions.create(
            model=self.settings.openrouter_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
```

侧边栏必须提供 API Key、Base URL、Model、测试连接按钮。API Key 默认只保存到 `st.session_state`，不要默认写入磁盘。

---

## 8. 文件发现模块

新增 `src/file_resolver.py`。

```python
from pathlib import Path

PDF_NAME = "（修正两处错误）马原知识点总结（2026春季学期）.pdf"
MD_FRONT_NAME = "马原前16页应试题库.md"
MD_BACK_NAME = "马原17-31页应试题库.md"


def resolve_data_file(filename: str, project_root: str | Path = ".") -> Path:
    root = Path(project_root).resolve()
    candidates = [root / filename, root / "data" / filename]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"未找到 {filename}。请把文件放到项目根目录或 data/ 目录。"
    )


def resolve_all_sources(project_root: str | Path = ".") -> dict[str, Path]:
    return {
        "pdf": resolve_data_file(PDF_NAME, project_root),
        "front_md": resolve_data_file(MD_FRONT_NAME, project_root),
        "back_md": resolve_data_file(MD_BACK_NAME, project_root),
    }
```

前端启动时展示：

```text
PDF：已找到 / 未找到
前16页题库样例：已找到 / 未找到
17-31页题库样例：已找到 / 未找到
```

如果两个 `.md` 题库缺失，系统仍可基于 PDF 出题，但必须提示“当前缺少风格样例，无法进入高仿题库模式”。

---

## 9. PDF 读取与知识库构建

### 9.1 PDF 解析

`src/pdf_loader.py`：

```python
import fitz
from dataclasses import dataclass

@dataclass
class PageText:
    page: int
    text: str

class PDFLoader:
    def load(self, pdf_path: str) -> list[PageText]:
        doc = fitz.open(pdf_path)
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            text = self._clean(text)
            pages.append(PageText(page=i, text=text))
        return pages

    def _clean(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            if s == "马克思主义基本原理知识点梳理":
                continue
            if s.isdigit():
                continue
            lines.append(s)
        return "\n".join(lines)
```

### 9.2 分块策略

`src/chunker.py`：

- 按章节标题优先切分；
- 每个 chunk 约 600-1000 中文字符；
- chunk 必须保留：`chunk_id`、`page_start`、`page_end`、`section_path`、`text`。

```python
from pydantic import BaseModel

class KnowledgeChunk(BaseModel):
    chunk_id: str
    page_start: int
    page_end: int
    section_path: str
    text: str
```

章节标题识别：

```python
HEADING_PATTERNS = [
    r"^[一二三四五六七八九十]+、.+$",
    r"^（[一二三四五六七八九十]+）.+$",
    r"^\d+\.\s*.+$",
]
```

### 9.3 PDF 检索器

`src/retriever.py` 使用 jieba + BM25：

```python
import jieba
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.tokenized = [list(jieba.cut(c.text)) for c in chunks]
        self.bm25 = BM25Okapi(self.tokenized)

    def search(self, query: str, top_k: int = 6):
        tokens = list(jieba.cut(query))
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self.chunks[i], float(score)) for i, score in ranked]
```

---

## 10. Markdown 样例题库解析

新增 `src/md_exam_loader.py`，这是本次修改的核心模块。它负责把两个样例 `.md` 题库变成可检索、可统计、可供 prompt 引用的“风格样例库”。

### 10.1 数据结构

```python
from typing import Optional, Literal
from pydantic import BaseModel

ExamRange = Literal["前16页", "17-31页", "全31页", "自定义"]
QuestionType = Literal["单项选择题", "多项选择题", "辨析题", "简答题", "论述题", "材料分析题"]

class ExampleQuestion(BaseModel):
    source_file: str
    exam_range: ExamRange
    type: QuestionType
    number: str
    stem: str
    options: list[str] = []
    material: Optional[str] = None
    sub_questions: list[str] = []
    answer: Optional[str] = None

class ExamStyleProfile(BaseModel):
    source_file: str
    title: str
    scope: str
    type_counts: dict[str, int]
    section_order: list[str]
    answer_style_notes: list[str]
    examples: list[ExampleQuestion]
```

### 10.2 解析目标

解析器至少要能抽取：

1. 标题与范围说明；
2. 六个题型章节；
3. 题目列表；
4. 选择题选项；
5. 材料分析题材料、问题；
6. 参考答案区；
7. 各题型题量统计。

### 10.3 简化解析策略

先把文件按 `# 参考答案` 分成题目区和答案区。

```python
def split_questions_and_answers(md: str) -> tuple[str, str]:
    marker = "# 参考答案"
    if marker not in md:
        return md, ""
    left, right = md.split(marker, 1)
    return left, marker + right
```

再按 `##` 二级标题切分章节。

```python
import re

SECTION_RE = re.compile(r"^##\s+(.+)$", re.M)

def split_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections
```

选择题、辨析题、简答题、论述题都可用行首编号 `1. ` 切分。材料分析题用 `**材料一**`、`**材料二**` 切分。

### 10.4 样例库用途

样例题库不是知识依据，而是用于：

1. 题型比例：默认题量模板；
2. 题干措辞：选择题、辨析题、简答题、论述题的常用句式；
3. 选项设计：相近概念干扰项；
4. 答案结构：客观题答案汇总、主观题分点式要点；
5. Markdown 导出格式：高度仿照原样例。

---

## 11. 风格检索器

新增 `src/style_retriever.py`。它从两个 `.md` 样例中检索相似题型和相似知识点的题目，给 prompt 提供“风格参考”。

```python
import jieba
from rank_bm25 import BM25Okapi

class StyleRetriever:
    def __init__(self, examples):
        self.examples = examples
        docs = [self._example_to_text(e) for e in examples]
        self.tokenized = [list(jieba.cut(d)) for d in docs]
        self.bm25 = BM25Okapi(self.tokenized)

    def _example_to_text(self, e):
        return "\n".join([
            e.type,
            e.stem or "",
            "\n".join(e.options or []),
            e.material or "",
            "\n".join(e.sub_questions or []),
            e.answer or "",
        ])

    def search(self, query: str, question_type: str | None = None, top_k: int = 5):
        tokens = list(jieba.cut(query))
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for i, score in ranked:
            e = self.examples[i]
            if question_type and e.type != question_type:
                continue
            results.append((e, float(score)))
            if len(results) >= top_k:
                break
        return results
```

Prompt 中引用样例时要明确：

```text
下面是风格样例，仅供模仿题型格式、措辞和答案结构，不得照抄题干、选项或答案。
```

---

## 12. 题目 JSON Schema

`src/schemas.py` 必须定义 Pydantic 模型。

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field

QuestionType = Literal["单项选择题", "多项选择题", "辨析题", "简答题", "论述题", "材料分析题"]
Difficulty = Literal["简单", "中等", "困难"]

class Question(BaseModel):
    id: str
    type: QuestionType
    chapter: str
    knowledge_point: str
    difficulty: Difficulty
    stem: str
    options: Optional[list[str]] = None
    material: Optional[str] = None
    sub_questions: Optional[list[str]] = None
    answer: str | list[str]
    explanation: str
    source_pages: list[int]
    source_quote: str = Field(description="来自 PDF 的简短依据，控制在 80 字以内")
    intention: str = Field(description="说明本题考查什么、为什么这样设干扰项")
    score: int = 0

class QuestionSet(BaseModel):
    title: str
    source_profile: str
    questions: list[Question]

class ExamBankMarkdownPlan(BaseModel):
    title: str
    scope: str
    type_order: list[QuestionType]
    type_counts: dict[QuestionType, int]
```

内部生成推荐先要求 LLM 输出 JSON，再由 `exporter.py` 渲染成仿样例 Markdown。不要直接让模型输出整篇 Markdown 作为唯一结果，否则难以校验。

---

## 13. 出题 Prompt 设计

`src/prompts.py` 集中管理 prompt。

### 13.1 系统 Prompt

```text
你是本科《马克思主义基本原理》课程命题助手。
你的任务是严格依据给定的 PDF 课程知识点材料生成考试题。
同时，你必须模仿给定 Markdown 应试题库样例的题型结构、题干措辞、选项风格和答案组织方式。
样例只用于模仿风格，不能照抄题干、选项、材料或答案。
不得引入材料外的新知识，不得使用未经 PDF 材料支持的表述。
命题风格应贴近本科期末考试：重概念、重关系、重辨析、重原理与方法论。
输出必须是合法 JSON，不要输出 Markdown。
```

### 13.2 单题/批量题生成 Prompt

```text
请根据“PDF课程材料片段”和“Markdown题库风格样例”，生成 {num_questions} 道 {question_type}。

一、配置
- 章节范围：{chapter}
- 页码范围：{page_range}
- 难度：{difficulty}
- 主要知识点：{knowledge_point}
- 题库模板：{style_profile_name}

二、硬性要求
1. 知识依据只能来自 PDF课程材料片段。
2. Markdown题库风格样例只用于模仿题型格式、措辞、干扰项风格和答案组织方式，禁止照抄。
3. 单项选择题：4 个选项，只有 1 个正确答案，题干尽量使用“是指/决定了/根本标准是/表现为/不包括”等样例化表达。
4. 多项选择题：4 个选项，至少 2 个正确答案，答案形如 ABC 或 ABCD。
5. 辨析题：题干应是常见错误或片面判断，答案以“正确/错误/不准确 + 理由 + 正确表述”组织。
6. 简答题：答案按“含义—内容—方法论”或分点要点组织。
7. 论述题：答案必须包含“原理阐述 + 现实意义/联系实际”。
8. 材料分析题：给出 120-250 字材料，设置 2 个小问，答案分点。
9. 每题必须给出 source_pages 和 source_quote。
10. 不要生成与样例题库完全相同的题干。

PDF课程材料片段：
{knowledge_context}

Markdown题库风格样例：
{style_examples}

请输出符合以下 JSON Schema 的 JSON：
{schema}
```

### 13.3 仿完整题库 Prompt

```text
请生成一份新的《马克思主义基本原理 应试题库》。

题库模板：{profile_name}
题型结构：{type_counts}
章节/页码范围：{chapters_or_pages}
难度比例：简单 {easy_ratio}，中等 {medium_ratio}，困难 {hard_ratio}

要求：
1. 题型顺序必须是：单项选择题、多项选择题、辨析题、简答题、论述题、材料分析题。
2. 先生成结构化 JSON，不要直接输出 Markdown。
3. 导出 Markdown 时由程序渲染为样例题库格式。
4. 客观题答案必须可汇总为类似“1.A　2.B　3.C”的格式。
5. 主观题参考答案必须模仿样例中的“要点式”写法。
6. 材料分析题必须模仿“**材料一** / **问题：** / （1）（2）”结构。
7. 不能复制样例原题；相似题必须换知识点、换设问或换干扰项。

PDF材料：
{knowledge_context}

题库风格摘要：
{style_summary}

相似风格样例：
{style_examples}

JSON Schema：
{schema}
```

---

## 14. 高频易混点库

`src/exam_profiles.py` 中内置“易混点库”，用于生成高质量客观题和辨析题。

```python
CONFUSING_PAIRS = [
    ("矛盾的同一性", "矛盾的斗争性", "同一性强调相互依存、相互吸引、相互贯通；斗争性强调相互排斥、相互否定、相互分离。"),
    ("矛盾的普遍性", "矛盾的特殊性", "普遍性强调共性、一般性、绝对性；特殊性强调个性、具体特点、有条件性。"),
    ("主要矛盾", "矛盾的主要方面", "主要矛盾是在矛盾体系中起决定作用的矛盾；矛盾主要方面是一对矛盾内部起主导作用的一方。"),
    ("运动", "静止", "运动是绝对的、无条件的；静止是相对的、有条件的。"),
    ("量变", "质变", "量变是必要准备，质变是必然结果。"),
    ("辩证否定观", "形而上学否定观", "辩证否定是扬弃，形而上学否定把肯定与否定绝对对立。"),
    ("真理的绝对性", "真理的相对性", "真理既有无条件、确定的一面，又有有条件、有限的一面。"),
    ("感性认识", "理性认识", "感性认识是认识的低级阶段，理性认识是认识的高级阶段，二者在实践基础上统一。"),
    ("社会存在", "社会意识", "社会存在决定社会意识，社会意识具有相对独立性。"),
    ("生产力", "生产关系", "生产力决定生产关系，生产关系反作用于生产力。"),
    ("经济基础", "上层建筑", "经济基础决定上层建筑，上层建筑反作用于经济基础。"),
    ("人民群众", "杰出人物", "人民群众是历史创造者，杰出人物作用离不开人民群众和历史条件。"),
    ("使用价值", "价值", "使用价值是自然属性，价值是商品特有的社会属性。"),
    ("具体劳动", "抽象劳动", "具体劳动创造使用价值，抽象劳动形成价值。"),
    ("绝对剩余价值", "相对剩余价值", "前者靠延长工作日或提高劳动强度，后者靠缩短必要劳动时间。"),
]
```

---

## 15. 前端界面设计

### 15.1 页面布局

```text
顶部：马原智能出题器
侧边栏：
  - OpenRouter API 配置
  - 三个资料文件状态
  - 模型参数
  - 检索参数
  - 导出设置
主页面 Tabs：
  1. 仿应试题库生成
  2. 单题/批量出题
  3. 易混概念专项
  4. 样例题库解析
  5. 知识库检索
  6. 历史记录/导出
```

### 15.2 Tab 1：仿应试题库生成

这是本项目的核心页面。

组件：

- 模板选择：
  - 前16页仿真题库；
  - 17-31页仿真题库；
  - 全31页综合题库；
  - 自定义小题库。
- 题量配置：默认读取模板题量，可手动改。
- 章节/页码范围：前16页、17-31页、全31页、手动页码。
- 难度比例：简单/中等/困难。
- 是否允许与样例同知识点不同设问。
- 生成按钮。
- 预览：题目版、答案版、完整 Markdown。
- 下载：`.md`、`.json`、`.csv`。

### 15.3 Tab 2：单题/批量出题

组件：

- 章节选择；
- 页码范围；
- 题型选择；
- 难度选择；
- 数量 slider；
- 自定义知识点输入；
- 风格模板选择：前16页样例 / 17-31页样例 / 自动匹配；
- 生成按钮。

结果卡片：

```text
【单项选择题｜中等｜p.8｜仿：前16页题库】
题干：……
A. ……
B. ……
C. ……
D. ……
答案：B
解析：……
知识点：……
命题意图：……
```

### 15.4 Tab 3：易混概念专项

组件：

- 下拉选择易混概念对；
- 题型组合：单选 + 多选 + 辨析 + 简答；
- 数量；
- 生成专项训练。

### 15.5 Tab 4：样例题库解析

用于让用户确认系统已经读懂两个 `.md`。

展示：

- 两个题库文件路径；
- 标题；
- 范围说明；
- 各题型题量；
- 随机展示 3 条样例题；
- 参考答案区是否解析成功；
- 材料分析题数量。

### 15.6 Tab 5：知识库检索

输入关键词后，同时展示：

1. PDF 知识命中：页码、章节、chunk 文本；
2. Markdown 风格命中：来源题库、题型、题干、答案片段。

### 15.7 Tab 6：历史记录/导出

保存每次生成结果到 `st.session_state["history"]`，支持查看、删除、全部导出。

---

## 16. Markdown 导出必须模拟两个题库

`src/exporter.py` 要实现 `export_exam_bank_markdown(question_set)`。

### 16.1 导出结构

```markdown
# 马克思主义基本原理 应试题库（自动生成）

> 范围：……
> 题型贴合本科马原期末出题习惯：单选、多选、辨析、简答、论述、材料分析。答案附在每部分末尾。

---

## 一、单项选择题

1. ……（　　）
   A. ……
   B. ……
   C. ……
   D. ……

## 二、多项选择题
...

## 三、辨析题（判断并说明理由）
...

## 四、简答题
...

## 五、论述题
...

## 六、材料分析题

**材料一**
……

**问题：**
（1）……
（2）……

---
---

# 参考答案

## 一、单项选择题

1.B　2.A　3.C

## 二、多项选择题

1.ABC　2.ABCD

## 三、辨析题（要点）

1. **错误。** ……
```

### 16.2 客观题答案汇总

实现函数：

```python
def format_objective_answer_key(questions):
    parts = []
    for i, q in enumerate(questions, start=1):
        ans = "".join(q.answer) if isinstance(q.answer, list) else str(q.answer)
        parts.append(f"{i}.{ans}")
    # 每 10 个换行，模仿样例紧凑排版
    lines = ["　".join(parts[i:i+10]) for i in range(0, len(parts), 10)]
    return "\n".join(lines)
```

### 16.3 主观题答案格式

辨析题答案：

```markdown
1. **错误。** 这是……。正确表述是……。
```

简答题答案：

```markdown
**1. 题目关键词**
①……；②……；③……。
```

论述题答案：

```markdown
**1. 原理 + 意义**
原理：……
意义：……
联系实际：……
```

材料分析答案：

```markdown
**材料一答案要点**
（1）……
（2）……
```

---

## 17. 出题质量控制

### 17.1 生成前控制

1. 根据章节/页码/知识点检索 PDF。
2. 根据题型/知识点检索 Markdown 样例。
3. Prompt 明确区分“知识依据”和“风格样例”。
4. 客观题 temperature 建议 0.2-0.4；主观题 0.3-0.6。

### 17.2 生成后校验

`src/validator.py` 必须检查：

1. JSON 能否解析；
2. 题目数量是否符合配置；
3. 题型是否属于六类；
4. 单选题是否 4 个选项且答案唯一；
5. 多选题是否 4 个选项且至少两个答案；
6. 辨析题答案是否以“正确/错误/不准确”之一开头；
7. 材料分析题是否有 `material` 和至少 2 个 `sub_questions`；
8. `source_pages` 是否为空；
9. `source_quote` 是否能在 PDF 检索上下文中找到；
10. 题干与两个样例题库中的题干相似度是否过高。

### 17.3 重复题检测

实现简单字符相似度或 difflib：

```python
from difflib import SequenceMatcher

def too_similar(a: str, b: str, threshold: float = 0.86) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= threshold
```

如果与样例题干相似度过高，则重试生成，并在 prompt 中追加：

```text
上一版题干与样例题库过于相似，请保留同一知识点，但更换设问角度、材料或干扰项。
```

### 17.4 幻觉抑制

每题必须带 `source_quote`，且该 quote 必须来自 PDF 检索片段。若不在 context 中出现，UI 用黄色警告“依据片段未直接命中，请人工复核”。第一版不强制失败，但导出时可标记。

---

## 18. 核心代码流程

`src/generator.py`：

```python
class QuestionGenerator:
    def __init__(self, knowledge_retriever, style_retriever, llm_client):
        self.knowledge_retriever = knowledge_retriever
        self.style_retriever = style_retriever
        self.llm = llm_client

    def generate_questions(self, config):
        knowledge_query = self._build_knowledge_query(config)
        knowledge_hits = self.knowledge_retriever.search(knowledge_query, top_k=config.knowledge_top_k)
        knowledge_context = self._format_knowledge_context(knowledge_hits)

        style_query = self._build_style_query(config)
        style_hits = self.style_retriever.search(
            style_query,
            question_type=config.question_type,
            top_k=config.style_top_k,
        )
        style_examples = self._format_style_examples(style_hits)

        prompt = build_question_prompt(config, knowledge_context, style_examples)
        raw = self.llm.chat(prompt, temperature=config.temperature)
        parsed = parse_and_validate(raw)
        validated = validate_against_sources(parsed, knowledge_context, style_hits)
        return validated

    def _build_knowledge_query(self, config):
        return " ".join([
            config.chapter or "",
            config.page_range or "",
            config.knowledge_point or "",
            config.question_type or "",
            config.difficulty or "",
        ])

    def _build_style_query(self, config):
        return " ".join([
            config.question_type or "",
            config.knowledge_point or "",
            config.chapter or "",
            "本科马原期末 应试题库",
        ])
```

完整题库生成时，不要一次性让模型生成 90 多道题。推荐按题型分批生成：

```text
单选题 10 道一批
多选题 10 道一批
辨析题 5 道一批
简答题 5 道一批
论述题 2 道一批
材料分析题 1 道一批
```

最后由程序合并、重新编号、统一导出。

---

## 19. README 要求

`README.md` 必须包含：

1. 项目简介；
2. 三个资料文件说明；
3. 环境安装；
4. OpenRouter API 配置；
5. 启动命令；
6. 使用流程；
7. “仿应试题库生成”说明；
8. 常见问题：
   - API Key 未配置；
   - PDF 未找到；
   - 两个 MD 样例未找到；
   - JSON 解析失败；
   - 生成题目与样例太像；
   - 题目不够贴近 PDF；
9. 安全说明：不要提交 `.env`。

---

## 20. 测试要求

### 20.1 `test_file_resolver.py`

检查：

- 根目录文件能被找到；
- `data/` 文件能被找到；
- 缺失时抛出清晰错误。

### 20.2 `test_pdf_loader.py`

检查：

- PDF 能读取；
- 页数大于 20；
- 文本中包含“马克思主义”；
- 能找到“矛盾的同一性”。

### 20.3 `test_md_exam_loader.py`

必须检查：

- 能读取两个 `.md`；
- 能识别六个题型章节；
- 前16页样例题量识别为：单选 40、多选 20、辨析 10、简答 14、论述 4、材料 3；
- 17-31页样例题量识别为：单选 45、多选 20、辨析 10、简答 15、论述 4、材料 3；
- 能解析客观题答案区；
- 能解析至少 1 道材料分析题。

### 20.4 `test_schema.py`

检查示例 JSON 能通过 Pydantic 校验。

### 20.5 `test_generator_prompt.py`

检查 prompt 中包含：

- “严格依据 PDF”；
- “Markdown题库风格样例只用于模仿”；
- “禁止照抄”；
- “输出 JSON”。

---

## 21. 验收标准

项目完成后，应满足：

1. `conda env create -f environment.yml` 成功；
2. `streamlit run app.py` 能打开本地网页；
3. 页面能检测 PDF 和两个 `.md` 文件；
4. “样例题库解析”页能显示两个样例的题型统计；
5. 用户配置 OpenRouter API Key 后，测试连接成功；
6. 用户选择“前16页仿真题库，小题量测试：单选 5、多选 3、辨析 2、简答 2、论述 1、材料 1”后，能生成结果；
7. 导出的 Markdown 结构与两个样例一致：题目在前、参考答案在后；
8. 客观题答案能汇总为 `1.A　2.B` 形式；
9. 主观题答案为要点式；
10. 材料分析题包含材料、问题和参考答案；
11. 每题含来源页码和 source_quote；
12. 与样例题干高度重复时系统能提示或重试；
13. 无 API Key 或文件缺失时 UI 不崩溃。

---

## 22. 实现优先级

### P0：必须完成

- Streamlit 前端；
- 文件发现；
- PDF 读取与 BM25 检索；
- 两个 Markdown 样例题库解析；
- OpenRouter 调用；
- 批量出题；
- JSON 校验；
- 仿样例 Markdown 导出。

### P1：建议完成

- 完整题库分批生成；
- 易混概念专项；
- 历史记录；
- CSV 导出；
- 重复题检测；
- 样例题库解析页面。

### P2：后续优化

- 本地向量检索；
- Word/PDF 导出；
- 错题本；
- 用户答题与自动评分；
- 知识点掌握度统计；
- 多 PDF、多课程扩展。

---

## 23. 给 Codex 的分步执行计划

请 Codex 按顺序实施：

1. 创建项目目录和基础文件；
2. 编写 `environment.yml`、`requirements.txt`、`.env.example`、`.gitignore`；
3. 实现 `file_resolver.py`；
4. 实现 `config.py`；
5. 实现 `pdf_loader.py`；
6. 实现 `md_exam_loader.py`，解析两个题库样例；
7. 实现 `chunker.py`；
8. 实现 `retriever.py` 和 `style_retriever.py`；
9. 实现 `schemas.py`；
10. 实现 `prompts.py`；
11. 实现 `openrouter_client.py`；
12. 实现 `validator.py`，包括 JSON 校验和重复题检测；
13. 实现 `exporter.py`，重点完成仿样例 Markdown；
14. 实现 `generator.py`，串联 PDF 检索、样例检索、LLM、校验；
15. 实现 `app.py`，完成前端交互；
16. 编写 README；
17. 编写基础测试；
18. 运行 `pytest` 和 `streamlit run app.py` 做最终检查。

---

## 24. 示例用户流程

1. 用户打开网页；
2. 侧边栏显示：PDF 已找到、前16页题库已找到、17-31页题库已找到；
3. 用户输入 OpenRouter API Key；
4. 点击“测试连接”，页面显示“连接成功”；
5. 进入“样例题库解析”，确认题量统计正常；
6. 进入“仿应试题库生成”；
7. 模板选择“前16页仿真题库”；
8. 选择“小题量测试”：单选 5、多选 3、辨析 2、简答 2、论述 1、材料 1；
9. 点击“生成”；
10. 页面展示题目版和答案版；
11. 用户点击“导出 Markdown”；
12. 导出的文件格式接近 `马原前16页应试题库.md`，但题目不与样例重复。

---

## 25. 最小可运行版本定义

MVP 只需完成：

1. conda 安装成功；
2. Streamlit 页面打开；
3. PDF 和两个 MD 自动检测；
4. MD 题库样例能解析并显示题量；
5. 用户能配置 OpenRouter API Key；
6. 用户能指定知识点生成 5 道“仿样例风格”的单选题；
7. 题目能显示答案、解析、来源页码；
8. 能导出一份结构类似样例题库的 Markdown。

MVP 完成后，再扩展完整题库、材料分析题批量生成和重复题自动重试。
