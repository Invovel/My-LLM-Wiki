# Wiki Log — 操作日志

> 格式: `YYYY-MM-DD HH:MM | 操作类型 | 摘要 | 涉及文件`
> 操作类型: INGEST | QUERY | LINT | DECAY | INDEX | RESEARCH

2026-05-07 15:20 | INDEX | 初始化 LLM Wiki 知识编译引擎 | wiki-purpose.md, wiki-schema.md, wiki-agent.md
2026-05-07 18:17 | RESEARCH | 首次深度研究：生物信息学前沿+博士申请规划 | summaries/source-bioinformatics-frontiers-2025.md, synthesis/synthesis-phd-application-bioinformatics.md, concepts/AI-protein-design.md, concepts/single-cell-spatial-omics.md, entities/Westlake-University.md, entities/West-China-School-Basic-Medical-Sciences.md
2026-05-07 18:26 | INGEST | 深度扩展：蛋白质设计/AI药物发现/生物学基础模型/工具数据库/中国研究者 | concepts/AI-protein-design.md, concepts/AI-drug-discovery.md, concepts/biology-foundation-models.md, entities/Beijing-Institute-of-Genomics.md, entities/David-Baker.md, entities/chinese-bioinformatics-researchers.md, entities/bioinformatics-tools-databases.md
2026-05-08 23:45 | FIX | 系统全面落地：修复 3 断链 (Patrick-Lewis, Knowledge-Intensive-NLP, Chinese-Academy-of-Sciences) | entities/Patrick-Lewis.md, concepts/Knowledge-Intensive-NLP.md, entities/Chinese-Academy-of-Sciences.md
2026-05-08 23:50 | FIX | 重写自动化脚本：hot_tracker.py + lint_checker.py 委托到 llm-wiki.py | scripts/hot_tracker.py, scripts/lint_checker.py
2026-05-08 23:52 | FIX | 修复 llm-wiki.py：Vault 路径自动检测、SOURCES_DIR→raw、log 路径、emoji 编码 | .llm-wiki/llm-wiki.py
2026-05-08 23:55 | FIX | 修复 llm-wiki.py 图谱分析：链接格式解析（路径标准化、双遍扫描） | .llm-wiki/llm-wiki.py
2026-05-08 23:58 | SYNC | 全量同步 + 热词更新 + 索引重建 | sync_state.json, hot_concepts.json, index.json, index.md
2026-05-09 00:00 | MAINT | 填充 overview.md、生成 Heat Report + Lint Report、清理 Review Queue | overview.md, System/Heat Report.md, System/Lint Report.md, System/Review Queue.md
2026-05-09 00:05 | STRUCT | 清理 wiki/ 空中文目录，添加说明 _README | 归档/, 概念/, 资料摘要/, 综合分析/
2026-05-09 00:10 | INGEST | Demo: MCP 协议录入 (两步 Ingest 演示) | summaries/source-mcp-protocol.md, concepts/Model-Context-Protocol.md, 更新 Retrieval-Augmented-Generation.md 交叉引用
2026-05-09 00:15 | DOC | 创建 System/操作手册.md — 完整日常使用指南 | System/操作手册.md
2026-05-09 00:20 | CLEANUP | 清理冗余：删除 4空中文目录 + 5废弃文件 + 3空资源目录 (26页→21实质内容) | 归档/, 概念/, 资料摘要/, 综合分析/, canvas/, wiki/assets/, raw/assets/, Wiki目录.md, 知识库概览.md, 操作日志.md, sortspec.md×2
2026-05-09 00:25 | FIX | 修复乱码：_update_frontmatter_field 换行缺失 + 7处 write_text 缺 encoding="utf-8" | llm-wiki.py
2026-05-09 00:30 | SKILL | 创建 .claude/skills/llm-wiki.md — 整合全部系统配置和操作协议为可加载 Skill | .claude/skills/llm-wiki.md, wiki-agent.md (更新引用)
