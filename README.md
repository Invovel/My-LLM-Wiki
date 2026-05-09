<p align="center">
  <a href="#english"><strong>English</strong></a> | <a href="#中文"><strong>中文</strong></a>
</p>

---

<a id="english"></a>

# LLM Wiki — Personal Knowledge Compilation Engine v2.0

> Automatically compile scattered inspirations, excerpts, and papers into a structured, continuously growing personal Wiki.
> Local Ollama models for preprocessing + Claude for deep analysis = Low-cost, high-intelligence knowledge management system.

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="python">
  <img src="https://img.shields.io/badge/Ollama-Qwen3.5%20%7C%20gemma4-orange" alt="ollama">
  <img src="https://img.shields.io/badge/license-MIT%20%7C%20Contact%20for%20Commercial%20Use-red" alt="license">
</p>

---

## Core Philosophy

Traditional RAG (Retrieval-Augmented Generation) follows an **"understand-on-retrieval"** approach — it temporarily assembles context for every query. LLM Wiki takes a different path: **"compile-on-ingest"** — it deeply processes knowledge, establishes connections, and generates structured pages when knowledge enters the system, allowing knowledge accumulation to produce a compound effect.

```
Traditional RAG:  Query → Retrieve → Temporary Assembly → Answer (Discarded after use)
LLM Wiki:        Input → Compile → Structured Wiki → Continuous Growth (Gets better with use)
```

---

## Architecture

```
🔧 Preprocessing Pipeline (Ollama Parallel)
Input → ├─ Keyword Extraction (Qwen3.5:4b)
      ├─ Entity Recognition   (Qwen3.5:4b)
      ├─ HyDE Enhancement    (gemma4:e2b)
      └─ Desensitization
      → Claude Deep Analysis
      → Generate Wiki Pages

📈 Hotword Maintenance (Four Stages)
Collection → Ollama Trend Analysis → Decay Update → Weekly Report Generation
```

### Division of Labor

| Role | Responsibilities | Advantages |
|------|------------------|------------|
| **Ollama (Local)** | Keyword extraction, entity recognition, HyDE enhancement, hotword trend analysis | Fast, free, offline |
| **Claude (Remote)** | Deep analysis, content generation, cross-referencing, complex decision-making | High intelligence, strong reasoning |
| **User** | Research direction, data sources, final confirmation | Domain expertise |

The system automatically falls back to Claude when Ollama is unavailable, without affecting core workflows.

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) (local model runtime)
- Obsidian (Wiki browser / editor)

### 2. Installation

```bash
git clone https://github.com/Invovel/My-LLM-Wiki.git my-wiki
cd my-wiki
bash setup.sh
```

### 3. Pull Ollama Models

```bash
ollama pull Qwen3.5:4b    # Keyword extraction / Entity recognition / Hotword maintenance
ollama pull gemma4:e2b    # HyDE query enhancement
```

### 4. Configuration

Edit `.llm-wiki/config.json`:

```json
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "models": {
      "keyword_extraction": "Qwen3.5:4b",
      "entity_recognition": "Qwen3.5:4b",
      "hyde_enhancement": "gemma4:e2b",
      "hotword_maintenance": "Qwen3.5:4b"
    }
  }
}
```

### 5. Testing

```bash
python scripts/ollama_test.py
python .llm-wiki/llm-wiki.py preprocess "Transformer architecture revolutionized NLP through self-attention mechanisms..."
```

---

## Usage Guide

### Import New Materials

```bash
# 1. Place materials in raw/inbox/
# 2. Ollama preprocessing
python .llm-wiki/llm-wiki.py preprocess "Material content..."

# 3. Claude generates Wiki pages based on preprocessing results
# (Trigger via Claude plugin in Obsidian, or manually feed preprocessing results to Claude)
```

### Fuzzy Query (HyDE)

```bash
python .llm-wiki/llm-wiki.py hyde "That paper about attention mechanisms..."
# → Ollama generates hypothetical document → Search knowledge base → Find matching pages
```

### Daily Maintenance

```bash
python scripts/hot_tracker.py       # Four-stage hotword maintenance
python scripts/lint_checker.py      # Health check (weekly)
python .llm-wiki/llm-wiki.py decay --auto  # L1-L2 automatic content reduction
```

### Command Cheat Sheet

| Command | Purpose |
|---------|---------|
| `llm-wiki.py preprocess <text>` | Ollama preprocessing (keywords + entities + desensitization) |
| `llm-wiki.py search <query> -k 10` | BM25 search + hotword bias |
| `llm-wiki.py hyde <idea>` | HyDE query enhancement |
| `llm-wiki.py hot collect` | Collect hotword data |
| `llm-wiki.py hot analyze` | Ollama trend analysis |
| `llm-wiki.py hot update` | Update hotness + apply decay |
| `llm-wiki.py hot report` | Generate hotword report |
| `llm-wiki.py sync` | Sync file SHA256 index |
| `llm-wiki.py graph` | Link graph analysis (orphans, hubs, communities) |
| `llm-wiki.py status` | Knowledge base health summary |
| `llm-wiki.py decay --auto` | L1-L2 automatic content reduction |
| `llm-wiki.py index` | Rebuild full library index |

---

## File Structure

```
Vault/
├── .claude/skills/llm-wiki.md   # Claude skill definition (core specification)
├── .llm-wiki/                    # Core engine
│   ├── llm-wiki.py               # CLI main program (with OllamaClient)
│   ├── config.json               # Ollama + preprocessing configuration
│   ├── sync_state.json           # SHA256 file index
│   └── index.json                # Structured index
├── scripts/                      # Automation scripts
│   ├── hot_tracker.py            # Hotword tracking (four stages)
│   ├── lint_checker.py           # Health check
│   ├── ollama_test.py            # Ollama connection test
│   └── init_vault.py             # Vault initialization
├── templates/                    # Wiki page templates
│   ├── concept.md                # Concept page template
│   ├── entity.md                 # Entity page template
│   ├── source.md                 # Source summary page template
│   └── synthesis.md              # Synthesis analysis page template
├── purpose.md                    # Research goals and scope
├── schema.md                     # Page specifications and quality standards
├── overview.md                   # Global overview
├── setup.sh                      # One-click initialization script
└── wiki/                         # Wiki pages (user knowledge content)
    ├── concepts/
    ├── entities/
    ├── summaries/
    └── synthesis/
```

---

## Hotword System

Fully automatic four-stage maintenance:

```
Collect citation counts, update times, access frequencies
  → Ollama (Qwen3.5:4b) trend analysis
    → Identify: Hot words / Emerging concepts / Plummeting words
      → Apply daily decay (×0.98), sync to page frontmatter
        → Generate Heat Report.md
```

**Hotness Formula:** `citation_count × 0.6 + recency × 0.2 + trend × 0.2`

**Five-level Content Decay:** From L1 (80% retention, automatic) to L5 (10% retention, requires confirmation), ensuring the knowledge base does not become bloated.

---

## Fallback Strategy

When Ollama is unavailable, the system automatically falls back:

- **Keyword Extraction** → Regular expressions + word frequency statistics
- **Entity Recognition** → Handled by Claude itself
- **HyDE Enhancement** → Save prompt templates for manual processing
- **Hotword Analysis** → Pure rule engine (citation count + time decay)

The core ingest process remains unaffected, only preprocessing speed decreases.

---

## Tech Stack

- **Python 3.10+** — CLI tools, BM25 search engine, hotword engine
- **Ollama** — Local model runtime (Qwen3.5:4b, gemma4:e2b)
- **Obsidian** — Markdown knowledge base frontend
- **Claude API** — Deep analysis and content generation

---

## License

This project is licensed under the **MIT License** with the following additional terms:

- **Personal Use**: Completely free, no authorization required.
- **Commercial Use**: **Must contact the author for authorization first.** Commercial use includes but is not limited to: using this system as part of a commercial product, providing paid services based on this system, deploying for profit within an enterprise.

📧 Commercial licensing inquiries: Contact via [GitHub Issues](https://github.com/Invovel/My-LLM-Wiki/issues).

---

## Contributing

Issues and Pull Requests are welcome.

Contribution directions:
- Add support for new Ollama models
- Optimize preprocessing prompt templates
- Improve hotword algorithms
- Extend page types and templates
- Multilingual support

---

<p align="center">
  <sub>Built with ❤️ by <a href="https://github.com/Invovel">Invovel</a> | Knowledge should grow, not pile up</sub>
</p>

---

<a id="中文"></a>

# LLM Wiki — 个人知识编译引擎 v2.0

> 将零散的灵感、文段、论文，自动编译为结构化、持续生长的个人 Wiki。
> 本地 Ollama 模型做预处理 + Claude 做深度分析 = 低成本、高智能的知识管理系统。

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="python">
  <img src="https://img.shields.io/badge/Ollama-Qwen3.5%20%7C%20gemma4-orange" alt="ollama">
  <img src="https://img.shields.io/badge/license-MIT%20%7C%20商业需联系-red" alt="license">
</p>

---

## 核心理念

传统 RAG（检索增强生成）是「检索时理解」——每次查询时临时拼凑上下文。LLM Wiki 走另一条路：**「入库时编译」**——在知识进入时就深度处理、建立关联、生成结构化页面，让知识积累产生复利效应。

```
传统 RAG:  查询 → 检索 → 临时拼接 → 回答（用完即弃）
LLM Wiki:  输入 → 编译 → 结构化 Wiki → 持续生长（越用越深）
```

---

## 架构

```
🔧 预处理流水线（Ollama 并行）
输入 → ├─ 关键词提取 (Qwen3.5:4b)
      ├─ 实体识别   (Qwen3.5:4b)
      ├─ HyDE 增强  (gemma4:e2b)
      └─ 去敏处理
      → Claude 深度分析
      → 生成 Wiki 页面

📈 热词维护（四阶段）
收集 → Ollama 分析趋势 → 更新衰减 → 生成周报
```

### 分工协议

| 角色 | 负责 | 优势 |
|------|------|------|
| **Ollama (本地)** | 关键词提取、实体识别、HyDE 增强、热词趋势分析 | 快速、免费、离线 |
| **Claude (远端)** | 深度分析、内容生成、交叉引用、复杂决策 | 高智能、强推理 |
| **用户** | 研究方向、资料来源、最终确认 | 领域判断 |

Ollama 不可用时自动降级到 Claude，不影响核心流程。

---

## 快速开始

### 1. 前置要求

- Python 3.10+
- [Ollama](https://ollama.com/download)（本地模型运行时）
- Obsidian（Wiki 浏览器 / 编辑器）

### 2. 安装

```bash
git clone https://github.com/Invovel/My-LLM-Wiki.git my-wiki
cd my-wiki
bash setup.sh
```

### 3. 拉取 Ollama 模型

```bash
ollama pull Qwen3.5:4b    # 关键词提取 / 实体识别 / 热词维护
ollama pull gemma4:e2b    # HyDE 查询增强
```

### 4. 配置

编辑 `.llm-wiki/config.json`：

```json
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "models": {
      "keyword_extraction": "Qwen3.5:4b",
      "entity_recognition": "Qwen3.5:4b",
      "hyde_enhancement": "gemma4:e2b",
      "hotword_maintenance": "Qwen3.5:4b"
    }
  }
}
```

### 5. 测试

```bash
python scripts/ollama_test.py
python .llm-wiki/llm-wiki.py preprocess "Transformer 架构通过自注意力机制改变了 NLP 领域..."
```

---

## 使用指南

### 导入新资料

```bash
# 1. 将资料放入 raw/收件箱/
# 2. Ollama 预处理
python .llm-wiki/llm-wiki.py preprocess "资料内容..."

# 3. Claude 根据预处理结果生成 Wiki 页面
# （在 Obsidian 中通过 Claude 插件触发，或手动让 Claude 读取预处理结果）
```

### 模糊查询

```bash
python .llm-wiki/llm-wiki.py hyde "那个关于注意力的论文..."
# → Ollama 生成假设文档 → 搜索知识库 → 找到匹配页面
```

### 日常维护

```bash
python scripts/hot_tracker.py              # 四阶段热词维护（每日推荐）
python scripts/lint_checker.py             # 健康检查（每周推荐）
python .llm-wiki/llm-wiki.py decay --auto  # L1-L2 自动内容缩减
```

### 命令速查

| 命令 | 用途 |
|------|------|
| `llm-wiki.py preprocess <text>` | Ollama 预处理（关键词+实体+去敏） |
| `llm-wiki.py search <query> -k 10` | BM25 搜索 + 热词偏置 |
| `llm-wiki.py hyde <idea>` | HyDE 查询增强 |
| `llm-wiki.py hot collect` | 收集热词数据 |
| `llm-wiki.py hot analyze` | Ollama 分析趋势 |
| `llm-wiki.py hot update` | 更新热度 + 衰减 |
| `llm-wiki.py hot report` | 生成热词报告 |
| `llm-wiki.py sync` | 同步文件 SHA256 索引 |
| `llm-wiki.py graph` | 链接图谱分析（孤岛、枢纽、社区） |
| `llm-wiki.py status` | 知识库健康摘要 |
| `llm-wiki.py decay --auto` | L1-L2 自动内容缩减 |
| `llm-wiki.py index` | 重建全库索引 |

---

## 文件结构

```
Vault/
├── .claude/skills/llm-wiki.md   # Claude 技能定义（核心规范）
├── .llm-wiki/                    # 核心引擎
│   ├── llm-wiki.py               # CLI 主程序（含 OllamaClient）
│   ├── config.json               # Ollama + 预处理配置
│   ├── sync_state.json           # SHA256 文件索引
│   └── index.json                # 结构化索引
├── scripts/                      # 自动化脚本
│   ├── hot_tracker.py            # 热词追踪（四阶段）
│   ├── lint_checker.py           # 健康检查
│   ├── ollama_test.py            # Ollama 连接测试
│   └── init_vault.py             # Vault 初始化
├── templates/                    # Wiki 页面模板
│   ├── concept.md                # 概念页模板
│   ├── entity.md                 # 实体页模板
│   ├── source.md                 # 来源摘要页模板
│   └── synthesis.md              # 综合分析页模板
├── purpose.md                    # 研究目标与范围
├── schema.md                     # 页面规范与质量标准
├── overview.md                   # 全局概览
├── setup.sh                      # 一键初始化脚本
└── wiki/                         # Wiki 页面（用户知识内容）
    ├── concepts/
    ├── entities/
    ├── summaries/
    └── synthesis/
```

---

## 热词系统

四阶段全自动维护：

```
收集引用计数、更新时间、访问频率
  → Ollama (Qwen3.5:4b) 分析趋势
    → 识别：热门词 / 新兴概念 / 暴跌词
      → 应用每日衰减 (×0.98)，同步到页面 frontmatter
        → 生成 Heat Report.md
```

**热度公式：** `citation_count × 0.6 + recency × 0.2 + trend × 0.2`

**五级内容衰减：** 从 L1（80% 保留，自动）到 L5（10% 保留，需确认），确保知识库不臃肿。

---

## 降级策略

Ollama 不可用时，系统自动降级：

- **关键词提取** → 正则 + 词频统计
- **实体识别** → Claude 自行处理
- **HyDE 增强** → 保存 prompt 模板供手动处理
- **热词分析** → 纯规则引擎（引用计数 + 时间衰减）

核心 Ingest 流程不受影响，只是预处理速度下降。

---

## 技术栈

- **Python 3.10+** — CLI 工具、BM25 搜索引擎、热词引擎
- **Ollama** — 本地模型运行时（Qwen3.5:4b, gemma4:e2b）
- **Obsidian** — Markdown 知识库前端
- **Claude API** — 深度分析与内容生成

---

## 许可证

本项目采用 **MIT 许可证**，但有以下附加条款：

- **个人使用**：完全免费，无需授权。
- **商业使用**：**必须先联系作者获得授权。** 商业用途包括但不限于：将本系统作为商业产品的一部分、提供基于本系统的付费服务、在企业内部以盈利为目的的部署。

📧 商业授权咨询：通过 [GitHub Issues](https://github.com/Invovel/My-LLM-Wiki/issues) 联系。

---

## 贡献

欢迎提交 Issue 和 Pull Request。

贡献方向：
- 新增 Ollama 模型支持
- 优化预处理 Prompt 模板
- 改进热词算法
- 扩展页面类型和模板
- 多语言支持

---

<p align="center">
  <sub>由 <a href="https://github.com/Invovel">Invovel</a> 用 ❤️ 构建 | 知识应该生长，而非堆积</sub>
</p>
