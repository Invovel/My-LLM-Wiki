#!/usr/bin/env python3
"""
初始化脚本：用于设置 Python 虚拟环境、安装依赖、配置 .env 等
"""
import subprocess
import sys

def main():
    print("正在初始化 llm-wiki-kit Python 环境...")
    subprocess.run([sys.executable, "-m", "venv", "venv"])
    subprocess.run(["./venv/bin/pip", "install", "python-frontmatter", "pyyaml"])
    print("初始化完成。请复制 .env.example 为 .env 并填写您的 API 密钥。")

if __name__ == "__main__":
    main()