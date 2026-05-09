<!-- 全局摘要（自动更新） -->

# 整体概览

> 此文件由自动化流程维护，请勿手动编辑。

最后更新：2026-05-08

---

## 📊 知识库统计

| 指标 | 数值 |
|------|------|
| **Wiki 页面总数** | 20（含 2 新） |
| 概念 (Concepts) | 7 |
| 实体 (Entities) | 8 |
| 摘要 (Summaries) | 2 |
| 综合分析 (Synthesis) | 1 |
| 问答归档 (Queries) | 0 |
| 平均置信度 | ~0.89 |
| 总链接数 | 60+ |

---

## 🔥 当前热度趋势

| 热词 | 热度 | 趋势 |
|------|------|------|
| Retrieval-Augmented Generation | ⬆️ 高 | 系统核心概念 |
| Dense Retrieval | ⬆️ 高 | 与 RAG 紧密关联 |
| AI 药物发现 | ➡️ 稳 | 持续关注 |
| AI 蛋白质设计 | ➡️ 稳 | 持续关注 |
| 生物学基础模型 | ➡️ 稳 | 持续关注 |
| 知识密集型 NLP | ⬆️ 新 | 通过 RAG 网络新建 |
| Patrick Lewis | ⬆️ 新 | RAG 关键人物，新建实体页 |

---

## 🕸️ 知识网络概览

### 两大主题集群

**1. 生物信息学 & 博士申请 (10 页)**
- 核心概念：AI 药物发现、AI 蛋白质设计、单细胞空间组学、生物学基础模型
- 关键实体：西湖大学、华西基础医学、北京基因组研究所、David Baker
- 综合分析：博士申请院校评估
- 原始资料：2024-2025 生物信息学前沿

**2. RAG & 检索系统 (8 页)**
- 核心概念：RAG、Dense Retrieval、知识密集型 NLP
- 关键实体：Facebook AI Research、Patrick Lewis
- 原始资料：RAG 论文 (2005.11401)
- 连接桥：Dense-Retrieval ↔ AI 蛋白质设计（向量搜索技术共享）

---

## ⚠️ 待处理事项

| 类型 | 数量 | 详情 |
|------|------|------|
| 断链 | 0 | 已修复 (2026-05-08) |
| 低置信度 (< 0.7) | 0 | — |
| 代码验证问题 | 0 | Dense-Retrieval 已确认通过 |
| 待确认缩减 | 0 | — |
| 孤立页面 | 待检查 | 运行 `llm-wiki graph` 确认 |

---

## 🔗 关键交叉链接

- [[wiki/concepts/Dense-Retrieval|Dense Retrieval]] ↔ [[wiki/concepts/Retrieval-Augmented-Generation|RAG]] ↔ [[wiki/concepts/Knowledge-Intensive-NLP|知识密集型 NLP]]
- [[wiki/entities/Facebook-AI-Research|FAIR]] → [[wiki/entities/Patrick-Lewis|Patrick Lewis]] → [[wiki/concepts/Retrieval-Augmented-Generation|RAG]]
- [[wiki/concepts/AI-drug-discovery|AI 药物发现]] ↔ [[wiki/concepts/AI-protein-design|AI 蛋白质设计]] ↔ [[wiki/concepts/biology-foundation-models|生物学基础模型]]
- [[wiki/synthesis/synthesis-phd-application-bioinformatics|博士申请评估]] → 所有生物信息学实体

---

## 📅 最近活动

| 日期 | 操作 |
|------|------|
| 2026-05-08 | FIX: 修复 2 断链 (Patrick-Lewis, Knowledge-Intensive-NLP) |
| 2026-05-08 | FIX: 重写 hot_tracker.py + lint_checker.py 脚本 |
| 2026-05-08 | FIX: 清理 Review Queue 过时代码验证条目 |
| 2026-05-07 | INDEX: 初始化 LLM Wiki 编译引擎 |
| 2026-05-07 | RESEARCH: 首次深度研究 — 生物信息学前沿 + 博士规划 |
| 2026-05-07 | INGEST: 深度扩展 — 蛋白质设计/AI 制药/生物基础模型 |
