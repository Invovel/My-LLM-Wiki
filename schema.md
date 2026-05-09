---
title: Wiki Schema
description: 页面类型、模板、质量标准、衰减规则、自动化契约
type: system
created: 2026-05-03
updated: 2026-05-07
---

# Wiki Schema（行为契约）

## 通用约定
- 所有页面必须使用 YAML frontmatter，字段见各模板
- 使用 `[[wikilinks]]` 进行双向链接，目标页面不存在时自动标记为待创建
- 页面正文统一使用 Markdown 格式，支持 Mermaid 图表
- 每次 Ingest 操作后必须更新 `index.md`、`log.md`、`overview.md`
- **`hotness` 字段由热词引擎自动维护**，不应手动填写；新建页面默认 `hotness: 0.0`

## 页面类型及模板

### 1. 来源摘要页（summaries/）
- **文件名**：`source-{简短英文关键词}.md`
- **目的**：将原文压缩至 30% 以下，同时保留全部核心论证
- **模板 frontmatter**：
  ```yaml
  ---
  type: summary
  tags: [来源类型, 主题]
  source: "原始资料标题或URL"
  author: "作者"
  date: 2026-05-03
  entities: ["实体名1", "实体名2"]
  concepts: ["概念名1"]
  confidence: 0.9
  reviewed: false
  ---
  ```
- **正文结构**：
  ```markdown
  # 资料标题
  ## 核心论点
  1. 论点1
  2. 论点2

  ## 关键实体
  - [[实体页]]
  ## 关键概念
  - [[概念页]]
  ## 与现有知识的连接
  - 补充了 [[某个概念]] 的 xxx 方面
  - 与 [[另一页面]] 的观点存在矛盾：...

  ## 对我研究的启发
  ...
  ```

### 2. 实体页（entities/）
- **文件名**：直接使用实体名，如 `llm-wiki.md`
- **目的**：记录具体的人、组织、项目、工具
- **模板 frontmatter**：
  ```yaml
  ---
  type: entity
  tags: [工具, 开源项目]
  aliases: ["中文名", "缩写"]
  sources: ["source-xxx.md"]
  created: 2026-05-03
  updated: 2026-05-03
  hotness: 0.0
  confidence: 0.8
  reviewed: false
  ---
  ```
- **正文结构**：
  ```markdown
  # 实体名
  ## 简述
  一句话描述。
  ## 核心功能/特点
  - 功能1
  ## 相关概念
  - [[概念页]]
  ## 相关实体
  - [[其他实体]]
  ## 知识缺口
  - 待研究：...
  ```

### 3. 概念页（concepts/）
- **文件名**：`概念名.md`（kebab-case 英文 slug）
- **目的**：定义抽象概念、方法论、范式。可独立阅读，不依赖原文
- **模板 frontmatter**：
  ```yaml
  ---
  type: concept
  tags: [方法论, AI]
  aliases: ["中文名", "同义词"]
  sources: ["source-xxx.md"]
  created: 2026-05-03
  updated: 2026-05-03
  hotness: 0.0
  confidence: 0.7
  reviewed: false
  parent_concepts: ["父概念名"]
  ---
  ```
- **正文结构**：
  ```markdown
  # 概念名
  ## 定义
  ...
  ## 关键原则/特征
  - ...
  ## 关系网络
  ```mermaid
  graph TD
    A[概念A] --> B[概念B]
    B --> C[概念C]
  ```
  ## 正例与反例
  - ✅ 正例
  - ❌ 反例
  ## 与相关概念的区别
  | 维度 | 本概念 | [[相似概念1]] | [[相似概念2]] |
  |------|--------|---------------|---------------|
  | ...  | ...    | ...           | ...           |
  ## 待探索维度
  - ...
  ```

### 4. 综合页（synthesis/）
- **文件名**：`synthesis-{主题}.md`
- **目的**：跨资料碰撞，综合多个来源生成新洞见
- **模板 frontmatter**：
  ```yaml
  ---
  type: synthesis
  tags: [综合, 主题]
  sources: ["source-a.md", "source-b.md"]
  created: 2026-05-03
  updated: 2026-05-03
  hotness: 0.0
  confidence: 0.7
  reviewed: false
  ---
  ```
- **正文结构**（与概念页类似，但强调跨资料碰撞）：
  ```markdown
  # 综合主题
  ## 问题背景
  ...
  ## 多源视角
  ### 视角A（来自 [[source-a]]）
  ...
  ### 视角B（来自 [[source-b]]）
  ...
  ## 矛盾与调和
  - 矛盾点1：A 认为 X，B 认为 Y
  - 调和方案：...
  ## 综合结论
  ...
  ## 剩余问题
  - ...
  ```

### 5. 问答归档（queries/）
- **文件名**：`query-{日期}-{关键词}.md`
- **模板 frontmatter**：
  ```yaml
  ---
  type: query
  question: "用户问题原文"
  date: 2026-05-03
  tags: [问答]
  confidence: 0.8
  ---
  ```
- **正文结构**：
  ```markdown
  # 问题
  > {用户问题原文}

  ## 综合回答
  ...

  ## 涉及页面
  - [[...]]
  ```

---

## 系统文件规范

### index.md（由 `llm-wiki index` 自动生成）
全库页面索引，按类型分组，每个条目格式：
```markdown
- [[页面名]] — 一句话描述 {#review 标记}
```

### overview.md（每次 Ingest 后更新）
全局知识摘要，格式：
```markdown
# 知识库概览 — YYYY-MM-DD
## 统计
- 总页面：N | 实体：N | 概念：N | 摘要：N | 综合：N
- 平均信心分：X.XX | 待审页面：N
- 热词 Top 5：[[A]], [[B]], ...

## 最近新增
- [[新页面]] — 内容摘要

## 知识空白
- 待研究：...

## 核心演化
- [[某概念]] 在过去 30 天内新增了 X 条关联
```

### log.md（每次操作后追加一行）
格式：`YYYY-MM-DD HH:MM | 操作类型 | 摘要 | 涉及文件列表`

操作类型：`INGEST | QUERY | LINT | DECAY | INDEX | RESEARCH`

---

## 质量标准与自动化规则

### 信心分（confidence）
- 区间：0.0 ~ 1.0
- **< 0.7**：自动添加标签 `#review` 并追加到 `System/Review Queue.md`
- **reviewed 字段**：人工审查后设为 `true`，同时可上调 confidence
- 来源摘要页：基于来源权威性与论证完整性评分
- 综合/概念页：基于交叉验证的数量和一致性评分

### 热力（hotness）
- **完全由热词引擎自动维护**，人工不干预
- 算法：被引用次数 × 0.6 + 最近编辑时间衰减 × 0.2 + 话题趋势 × 0.2
- 值域：0.0 ~ 1.0
- 每次 `llm-wiki hot update` 刷新，每日衰减 ×0.98

### 衰减与缩减 — 五层体系

| 层级 | 比率 | 触发条件 | 操作 |
|------|------|----------|------|
| L1 | 80% | `hotness < 0.7` 且 30 天未编辑 | 去冗余表述，自动执行 |
| L2 | 60% | `hotness < 0.5` 且 45 天未编辑 | 合并同类项，自动执行 |
| L3 | 40% | `hotness < 0.3` 且 60 天未编辑 | 保留核心论点+关键例证，需人工确认 |
| L4 | 20% | `hotness < 0.2` 且 75 天未编辑 | 只留结论框架，需人工确认 |
| L5 | 10% | `hotness < 0.15` 且 90 天未编辑 | 仅保留 frontmatter + 一句摘要，需人工确认 |

- **L1-L2 自动执行**，结果保存到 `System/Archive/`，原始文件保留
- **L3-L5 生成候选稿**，追加到 `System/Review Queue.md` 等待确认
- 缩减后页面仍在 `wiki/` 中保留完整链接关系

### 代码块验证（`#executable`）
- 标记 `#executable` 的代码块，由 cron 作业定期在沙箱中运行
- 比对输出与文档声称的行为
- 验证失败自动追加到 Review Queue

### 知识演化史
- 利用 Git 版本历史（Vault 已初始化 Git）
- 每月生成核心概念页（`hotness > 0.5`）的演化综述
- 格式：`System/Evolution/{概念名}-evolution.md`

### 矛盾追踪
- synthesis 页必须包含"矛盾与调和"章节
- 两个独立来源对同一 topic 持有不同观点时，在 synthesis 中显式标注
- 矛盾点在 lint 检查中被标记为 "contradiction" 严重级别，需人工审查

---

## 禁止行为
- 不得在未标记的情况下删除原始论点
- 不得在缩减过程中扭曲原意
- 所有自动修改都必须在 `log.md` 中留下记录
- 不得修改 `raw/` 和 `sources/` 下的原始文件
- 禁止在未标注的情况下混淆 LLM 生成内容与个人原创观点
