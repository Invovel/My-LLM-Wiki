#!/usr/bin/env python3
"""
Ollama 连接测试脚本

测试项目：
1. Ollama 服务是否可达
2. 所需模型是否已安装 (Qwen3.5:4b, gemma4:e2b)
3. 关键词提取是否正常
4. HyDE 增强是否正常
"""
import json
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT_ROOT / ".llm-wiki"))

try:
    import requests
except ImportError:
    print("[ERROR] 需要安装 requests 库: pip install requests")
    sys.exit(1)

# Import OllamaClient from llm-wiki
try:
    from llm_wiki import OllamaClient, CONFIG
except ImportError:
    # Fallback direct import path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "llm_wiki", str(VAULT_ROOT / ".llm-wiki" / "llm-wiki.py"))
    llm_wiki = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(llm_wiki)
    OllamaClient = llm_wiki.OllamaClient
    CONFIG = llm_wiki.load_config()

REQUIRED_MODELS = ["Qwen3.5:4b", "gemma4:e2b"]


def test_connection(client: OllamaClient) -> bool:
    """测试 Ollama 服务连接"""
    print("[1/4] 测试 Ollama 服务连接...")
    try:
        if client.is_available():
            print("  ✅ Ollama 服务可达")
            return True
        else:
            print("  ❌ Ollama 服务不可达")
            return False
    except Exception as e:
        print(f"  ❌ 连接异常: {e}")
        return False


def test_models(client: OllamaClient) -> bool:
    """测试所需模型是否已安装"""
    print("[2/4] 检查所需模型...")
    installed = client.list_models()
    if not installed:
        print("  ⚠️  无法获取模型列表（服务可能未运行）")
        return False

    all_ok = True
    for required in REQUIRED_MODELS:
        # Match exact or with tag suffix
        found = any(required in m or m.startswith(required.split(":")[0]) for m in installed)
        if found:
            print(f"  ✅ {required} 已安装")
        else:
            print(f"  ❌ {required} 未安装 — 请运行: ollama pull {required}")
            all_ok = False
    return all_ok


def test_keyword_extraction(client: OllamaClient) -> bool:
    """测试关键词提取"""
    print("[3/4] 测试关键词提取 (Qwen3.5:4b)...")
    test_text = "Transformer 架构通过自注意力机制（Self-Attention）彻底改变了自然语言处理领域。BERT 和 GPT 系列模型均基于此架构。"
    try:
        keywords = client.extract_keywords(test_text)
        if keywords:
            print(f"  ✅ 关键词提取成功: {json.dumps(keywords, ensure_ascii=False)}")
            return True
        else:
            print("  ⚠️  关键词提取返回空结果")
            return False
    except Exception as e:
        print(f"  ❌ 关键词提取失败: {e}")
        return False


def test_hyde(client: OllamaClient) -> bool:
    """测试 HyDE 查询增强"""
    print("[4/4] 测试 HyDE 查询增强 (gemma4:e2b)...")
    test_query = "如何提高 RAG 系统的检索精度？"
    try:
        hyde_doc = client.hyde_enhance(test_query)
        if hyde_doc and len(hyde_doc) > 50:
            print(f"  ✅ HyDE 生成成功 ({len(hyde_doc)} 字符)")
            print(f"  预览: {hyde_doc[:150]}...")
            return True
        else:
            print("  ⚠️  HyDE 生成结果过短")
            return False
    except Exception as e:
        print(f"  ❌ HyDE 生成失败: {e}")
        return False


def main():
    print("=" * 60)
    print("LLM Wiki — Ollama 连接测试")
    print("=" * 60)
    print(f"服务地址: {CONFIG.get('ollama', {}).get('base_url', 'http://localhost:11434')}")
    print()

    client = OllamaClient()
    results = []

    results.append(("服务连接", test_connection(client)))
    if not results[-1][1]:
        print("\n❌ Ollama 服务不可用，请确保已运行: ollama serve")
        print("后续测试跳过。")
        return

    results.append(("模型检查", test_models(client)))
    results.append(("关键词提取", test_keyword_extraction(client)))
    results.append(("HyDE 增强", test_hyde(client)))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    all_ok = True
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {status} — {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n✅ 所有测试通过！Ollama 集成已就绪。")
    else:
        print("\n⚠️  部分测试未通过，请检查上述失败项目。")


if __name__ == "__main__":
    main()
