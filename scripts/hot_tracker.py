#!/usr/bin/env python3
"""
热词追踪脚本：四阶段热词维护流程

阶段 1: collect  — 收集全库引用、更新时间、访问频率
阶段 2: analyze  — Ollama (Qwen3.5:4b) 分析趋势、识别新兴概念
阶段 3: update   — 应用衰减、更新 hot_concepts.json、同步页面 hotness
阶段 4: report   — 生成 Heat Report.md（Top 20、新兴概念、暴跌热词）

由 n8n Scheduled_Maintenance 工作流每日触发。
等价于：
  python .llm-wiki/llm-wiki.py hot update
  python .llm-wiki/llm-wiki.py hot report
"""
import subprocess
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
LLM_WIKI = VAULT_ROOT / ".llm-wiki" / "llm-wiki.py"


def run_llm_wiki(*args, capture: bool = True):
    """Run an llm-wiki subcommand."""
    result = subprocess.run(
        [sys.executable, str(LLM_WIKI)] + list(args),
        cwd=str(VAULT_ROOT),
        capture_output=capture,
        text=True,
    )
    if result.returncode != 0 and result.stderr:
        print(f"[WARN] llm-wiki {' '.join(args)}: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout.strip() if capture else ""


def run():
    if not LLM_WIKI.exists():
        print(f"[ERROR] llm-wiki.py not found at {LLM_WIKI}", file=sys.stderr)
        sys.exit(1)

    # ── 阶段 1: 收集数据 ──
    print("=" * 60)
    print("阶段 1/4: 收集热词数据 (collect)")
    print("=" * 60)
    output = run_llm_wiki("hot", "collect")
    print(output[:500] if len(output) > 500 else output)

    # ── 阶段 2: Ollama 分析趋势 ──
    print("\n" + "=" * 60)
    print("阶段 2/4: Ollama 分析趋势 (analyze)")
    print("=" * 60)
    output = run_llm_wiki("hot", "analyze")
    print(output[:500] if len(output) > 500 else output)

    # ── 阶段 3: 更新热词 ──
    print("\n" + "=" * 60)
    print("阶段 3/4: 更新热度分数 (update)")
    print("=" * 60)
    output = run_llm_wiki("hot", "update")
    print(output)

    # ── 阶段 4: 生成报告 ──
    print("\n" + "=" * 60)
    print("阶段 4/4: 生成热词报告 (report)")
    print("=" * 60)
    output = run_llm_wiki("hot", "report")
    print(output[:1000] if len(output) > 1000 else output)

    print("\n" + "=" * 60)
    print("热词追踪完成 — Heat Report.md 已更新")
    print("=" * 60)


if __name__ == "__main__":
    run()
