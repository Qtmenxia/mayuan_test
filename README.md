# 马原智能出题器

本项目是一个本地运行的 Python Web 应用，用 PDF 作为知识依据，用两份 Markdown 应试题库作为命题风格样例，并通过 OpenRouter Chat Completions 生成《马克思主义基本原理》应试题库。

## 资料文件

程序会优先在项目根目录查找资料文件，找不到时再查找 `data/`：

- `（修正两处错误）马原知识点总结（2026春季学期）.pdf`
- `马原前16页应试题库.md`
- `马原17-31页应试题库.md`

PDF 用于知识依据、页码来源和 `source_quote`；两份 Markdown 只用于模仿题型结构、答案组织和考试化表达，生成时禁止照抄原题。

## 安装

```bash
conda env create -f environment.yml
conda activate mayuan-qgen
```

也可以使用 pip：

```bash
pip install -r requirements.txt
```

Windows 本地虚拟环境建议直接放在项目目录，避免写到 C 盘：

```powershell
python -m venv F:\programs\mayuan_test\.venv
F:\programs\mayuan_test\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## OpenRouter 配置

复制 `.env.example` 为 `.env`，填写：

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=deepseek/deepseek-chat
```

当前根目录已有 `.env` 时，应用会自动读取。不要提交 `.env`。

## 启动

```bash
streamlit run app.py
```

打开页面后，侧边栏会显示 PDF 和两份 Markdown 样例的检测状态，也可以临时覆盖 OpenRouter 的 API Key、Base URL 和模型。

## 使用流程

1. 在侧边栏确认三个资料文件均已找到。
2. 点击“测试连接”确认 OpenRouter 可用。
3. 进入“样例题库解析”确认题量统计正常。
4. 进入“仿真题库生成”，选择前16页、17-31页、全31页或自定义小题库。
5. 选择页码范围、章节、难度和题量，点击生成。
6. 在预览区检查题目版、答案版和完整 Markdown。
7. 导出 Markdown、JSON 或 CSV。

## 主要能力

- 自动读取根目录或 `data/` 中的资料文件。
- 解析 PDF 并保留页码，构建本地 BM25 检索。
- 解析两份 Markdown 样例题库，统计六类题型并抽取风格样例。
- 支持单选、多选、辨析、简答、论述、材料分析六类题型。
- 生成结果包含答案、解析/要点、知识点、章节、来源页码、`source_quote` 和命题意图。
- Markdown 导出采用“先题目、后参考答案”的样例题库结构。

## 常见问题

- API Key 未配置：在侧边栏填写，或在 `.env` 中设置 `OPENROUTER_API_KEY`。
- PDF 未找到：把 PDF 放到项目根目录或 `data/`。
- Markdown 样例未找到：把两份题库 `.md` 放到项目根目录或 `data/`。
- JSON 解析失败：降低 temperature，减少单批题量后重试。
- 题目与样例太像：系统会给出校验提示，建议换知识点或降低同知识点仿写强度。
- 题目不贴近 PDF：检查 `source_quote` 和来源页码，必要时缩小页码范围或明确知识点。

## 测试

```bash
pytest
```
