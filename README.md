# LLM Wiki — 个人知识编译引擎 v2.0

> 将零散的灵感、文段、论文，自动编译为结构化、持续生长的个人 Wiki。
> 本地 Ollama 模型做预处理 + Claude 做深度分析 = 低成本、高智能的知识管理系统。

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="python">
  <img src="https://img.shields.io/badge/Ollama-Qwen3.5%20%7C%20gemma4-orange" alt="ollama">
  <img src="https://img.shields.io/badge/license-MIT%20%7C%20%E5%95%86%E7%94%A8%E9%9C%80%E8%81%94%E7%B3%BB-red" alt="license">
</p>

---

## 核心理念

传统的 RAG（检索增强生成）是「检索时理解」——每次查询时临时拼凑上下文。LLM Wiki 走另一条路：**「入库时编译」**——在知识进入时就深度处理、建立关联、生成结构化页面，让知识积累产生复利效应。

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
# 克隆仓库
git clone https://github.com/Invovel/My-LLM-Wiki.git my-wiki
cd my-wiki

# 一键初始化（安装依赖 + 拉取 Ollama 模型）
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
# 测试 Ollama 连接
python scripts/ollama_test.py

# 测试预处理
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
# HyDE: 将模糊想法转为假设文档，再用假设文档去搜索
python .llm-wiki/llm-wiki.py hyde "那个关于注意力的论文..."
# → Ollama 生成假设文档 → 搜索知识库 → 找到匹配页面
```

### 日常维护

```bash
# 四阶段热词维护（每日推荐）
python scripts/hot_tracker.py

# 健康检查（每周推荐）
python scripts/lint_checker.py

# 内容衰减（L1-L2 自动）
python .llm-wiki/llm-wiki.py decay --auto
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
| `llm-wiki.py graph` | 链接图谱分析 |
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

**五级内容衰减：** 从 L1（80%保留，自动）到 L5（10%保留，需确认），确保知识库不臃肿。

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
- **商业使用**：**必须先联系作者获得授权**。商业用途包括但不限于：将本系统作为商业产品的一部分、提供基于本系统的付费服务、在企业内部以盈利为目的的部署。

📧 商业授权咨询：通过 GitHub Issues 联系。

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
  <sub>Built with ❤️ by <a href="https://github.com/Invovel">Invovel</a> | 知识应该生长，而非堆积</sub>
</p>
