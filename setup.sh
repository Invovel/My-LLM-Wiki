#!/bin/bash
# llm-wiki-kit v2.0 — 一键初始化脚本 (Linux/macOS)
# 包含 Python 环境、依赖安装、Ollama 模型拉取
set -e

echo "============================================"
echo " LLM Wiki v2.0 — 环境初始化"
echo "============================================"
echo ""

# ── 1. Python 环境 ──
echo "[1/5] 设置 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install requests python-frontmatter pyyaml -q
echo "  ✅ Python 环境就绪"

# ── 2. 环境变量 ──
echo "[2/5] 配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ⚠️  请编辑 .env 文件填入您的 API 密钥"
else
    echo "  ✅ .env 已存在，跳过"
fi

# ── 3. Ollama 安装检查 ──
echo "[3/5] 检查 Ollama..."
if command -v ollama &> /dev/null; then
    echo "  ✅ Ollama 已安装"
else
    echo "  ⚠️  Ollama 未安装，正在安装..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "  ✅ Ollama 安装完成"
fi

# ── 4. Ollama 模型拉取 ──
echo "[4/5] 拉取 Ollama 模型..."
# 检查服务是否运行
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  启动 Ollama 服务..."
    ollama serve &
    sleep 3
fi

echo "  拉取 Qwen3.5:4b (关键词提取/实体识别/热词维护)..."
ollama pull Qwen3.5:4b

echo "  拉取 gemma4:e2b (HyDE 查询增强)..."
ollama pull gemma4:e2b

echo "  ✅ 模型拉取完成"

# ── 5. 初始化 Vault ──
echo "[5/5] 初始化知识库..."
python scripts/init_vault.py
echo "  ✅ Vault 初始化完成"

# ── 验证 ──
echo ""
echo "============================================"
echo " 验证安装"
echo "============================================"
echo ""
echo "测试 Ollama 连接..."
python scripts/ollama_test.py

echo ""
echo "============================================"
echo " 🚀 LLM Wiki v2.0 初始化完成！"
echo "============================================"
echo ""
echo "快速开始:"
echo "  预处理文本:    python .llm-wiki/llm-wiki.py preprocess \"你的文本\""
echo "  每日热词维护:  python scripts/hot_tracker.py"
echo "  健康检查:      python scripts/lint_checker.py"
echo ""
