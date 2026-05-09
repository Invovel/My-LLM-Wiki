#!/usr/bin/env python3
"""
健康检查脚本：调用 llm-wiki 引擎检测断链、孤立页面、缺失 frontmatter、
代码验证状态，并生成 Lint Report.md。

由 n8n Scheduled_Maintenance 工作流每周触发。
等价于：
  python .llm-wiki/llm-wiki.py graph   (断链 + 孤立检测)
  python .llm-wiki/llm-wiki.py status  (frontmatter + 置信度检查)
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
LLM_WIKI = VAULT_ROOT / ".llm-wiki" / "llm-wiki.py"
SYSTEM_DIR = VAULT_ROOT / "System"
LINT_REPORT = SYSTEM_DIR / "Lint Report.md"


def run_llm_wiki(*args) -> dict | None:
    """Run an llm-wiki subcommand and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, str(LLM_WIKI)] + list(args),
        cwd=str(VAULT_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[WARN] llm-wiki {' '.join(args)} returned {result.returncode}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # hot report outputs markdown, not JSON
        return None


def generate_lint_report(graph_data: dict | None, status_data: dict | None) -> str:
    """Generate a human-readable lint report from graph + status data."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 健康检查报告 — {now}",
        "",
        "> 自动生成，检查断链、孤立页面、frontmatter 完整性和代码验证状态。",
        "",
    ]

    # ── Broken Links ──
    wanted = graph_data.get("wanted_pages", []) if graph_data else []
    lines.append("## 断链")
    lines.append("")
    if wanted:
        for page in wanted[:30]:
            lines.append(f"- [[{page}]]")
    else:
        lines.append("✅ 未检测到断链。")
    lines.append("")

    # ── Orphan Pages ──
    orphans = graph_data.get("orphans", []) if graph_data else []
    lines.append("## 孤立页面")
    lines.append("")
    if orphans:
        lines.append(f"共 {len(orphans)} 个孤立页面：")
        for page in orphans[:30]:
            lines.append(f"- [[{page}]]")
    else:
        lines.append("✅ 所有页面均有入链或出链。")
    lines.append("")

    # ── Hubs ──
    hubs = graph_data.get("hubs", []) if graph_data else []
    lines.append("## 枢纽页面 (Top 10)")
    lines.append("")
    if hubs:
        for h in hubs[:10]:
            lines.append(f"- [[{h.get('page', '?')}]] — {h.get('links', 0)} 条链接")
    lines.append("")

    # ── Frontmatter Issues ──
    if status_data:
        missing_fm = status_data.get("missing_frontmatter", [])
        lines.append("## Frontmatter 问题")
        lines.append("")
        if missing_fm:
            for page in missing_fm:
                lines.append(f"- ❌ 缺少 frontmatter: [[{page}]]")
        else:
            lines.append("✅ 所有页面均有完整 frontmatter。")
        lines.append("")

        # ── Low Confidence ──
        low_conf = status_data.get("low_confidence_pages", [])
        lines.append("## 低置信度页面 (< 0.7)")
        lines.append("")
        if low_conf:
            for page in low_conf:
                lines.append(f"- #review [[{page}]]")
        else:
            lines.append("✅ 无低置信度页面。")
        lines.append("")

    # ── Code Verification ──
    lines.append("## 代码验证")
    lines.append("")
    lines.append("请运行 `python .llm-wiki/llm-wiki.py status` 并检查 `#executable` 代码块状态。")
    lines.append("")

    # ── General Stats ──
    if status_data:
        lines.append("## 概览")
        lines.append("")
        lines.append(f"- Wiki 页面数: {status_data.get('wiki_pages', '?')}")
        lines.append(f"- 原始资料数: {status_data.get('source_files', '?')}")
        lines.append(f"- 平均置信度: {status_data.get('avg_confidence', '?')}")
        lines.append(f"- 上次同步: {status_data.get('last_sync', '?')}")
        lines.append("")

    return "\n".join(lines)


def run():
    if not LLM_WIKI.exists():
        print(f"[ERROR] llm-wiki.py not found at {LLM_WIKI}", file=sys.stderr)
        sys.exit(1)

    print("=== 健康检查: 图谱分析 (断链 + 孤立页面) ===")
    graph_data = run_llm_wiki("graph")

    print("\n=== 健康检查: 状态扫描 (frontmatter + 置信度) ===")
    status_data = run_llm_wiki("status")

    print("\n=== 生成 Lint Report ===")
    report = generate_lint_report(graph_data, status_data)
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    LINT_REPORT.write_text(report, encoding="utf-8")
    print(f"Lint Report 已写入: {LINT_REPORT}")

    print("\n健康检查完成")


if __name__ == "__main__":
    run()
