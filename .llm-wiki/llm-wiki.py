#!/usr/bin/env python3
"""
llm-wiki CLI — 知识编译引擎命令行工具 v2.0
集成 Ollama 本地模型进行预处理和热词分析

用法: llm-wiki <command> [args...]

命令:
  preprocess <text>     Ollama 预处理：关键词提取 + 实体识别 + 去敏
  search <query>        BM25 关键词搜索 + 热词偏置
  hyde <idea>           生成假设文档用于查询扩展
  sync                 扫描 vault，更新 SHA256 索引
  graph                链接分析：孤岛、枢纽、社区
  status               统计 + 健康摘要
  hot <action>         热词追踪：collect / analyze / update / report
  decay                分级缩减：冷却内容按比例压缩
  index                重建全库索引
"""
import sys
import os
import json
import re
import hashlib
import time
import math
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

# ── Config ───────────────────────────────────────────────────────────
_script_dir = Path(__file__).resolve().parent
_default_vault = _script_dir.parent
VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", str(_default_vault)))
WIKI_DIR = VAULT / "wiki"
SYSTEM_DIR = VAULT / "System"
SOURCES_DIR = VAULT / "raw"
STATE_DIR = VAULT / ".llm-wiki"
INDEX_FILE = STATE_DIR / "index.json"
SYNC_STATE = STATE_DIR / "sync_state.json"
HOT_FILE = SYSTEM_DIR / "hot_concepts.json"
CONFIG_FILE = STATE_DIR / "config.json"
CONFIG_TOML = STATE_DIR / "config.toml"

for d in [SYSTEM_DIR, STATE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load config from JSON (preferred) or TOML (legacy fallback)."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            pass
    if CONFIG_TOML.exists():
        try:
            text = CONFIG_TOML.read_text(encoding="utf-8")
            cfg = {}
            for line in text.split("\n"):
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip().strip('"').strip("'")
            return {"legacy": cfg}
        except Exception:
            pass
    return _default_config()


def _default_config() -> dict:
    return {
        "ollama": {
            "base_url": "http://localhost:11434",
            "models": {
                "keyword_extraction": "Qwen3.5:4b",
                "entity_recognition": "Qwen3.5:4b",
                "hyde_enhancement": "gemma4:e2b",
                "hotword_maintenance": "Qwen3.5:4b",
            },
            "timeout": 30,
            "max_retries": 3,
        },
        "preprocessing": {
            "max_keywords": 15,
            "max_entities": 20,
            "enable_hyde": True,
            "enable_desensitization": True,
        },
    }


CONFIG = load_config()


# ── Ollama Client ─────────────────────────────────────────────────────
class OllamaClient:
    """Ollama 本地模型客户端"""

    def __init__(self):
        ollama_cfg = CONFIG.get("ollama", {})
        self.base_url = ollama_cfg.get("base_url", "http://localhost:11434")
        self.timeout = ollama_cfg.get("timeout", 30)
        self.max_retries = ollama_cfg.get("max_retries", 3)

    def _call(self, model: str, prompt: str, **kwargs) -> str:
        """调用 Ollama API，带指数退避重试"""
        try:
            import requests
        except ImportError:
            raise Exception("需要安装 requests 库: pip install requests")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.3),
                "top_p": kwargs.get("top_p", 0.9),
                "num_predict": kwargs.get("num_predict", 1000),
            },
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise Exception(f"Ollama API 调用失败: {e}")

    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """列出已安装的模型"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
        except Exception:
            pass
        return []

    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        models = CONFIG["ollama"]["models"]
        model = models.get("keyword_extraction", "Qwen3.5:4b")
        max_kw = CONFIG["preprocessing"].get("max_keywords", 15)

        prompt = f"""你是一个专业的关键词提取专家。请从以下文本中提取最重要的关键词。

要求：
1. 提取 5-{max_kw} 个关键词
2. 优先提取：技术术语、概念名称、方法论、工具名称
3. 忽略：通用词汇、停用词、时间词
4. 按重要性排序
5. 输出格式：JSON 数组

文本内容：
{text[:2000]}

输出示例：
["transformer", "attention mechanism", "self-attention", "NLP", "BERT"]"""

        try:
            response = self._call(model, prompt)
            keywords = json.loads(response)
            return keywords if isinstance(keywords, list) else []
        except Exception:
            return []

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """识别实体"""
        models = CONFIG["ollama"]["models"]
        model = models.get("entity_recognition", "Qwen3.5:4b")

        prompt = f"""你是一个专业的实体识别专家。请从以下文本中识别所有重要实体。

实体类型：
- 人物：研究者、作者、专家
- 组织：公司、机构、实验室
- 工具：软件、框架、库
- 项目：具体项目名称、产品
- 论文：研究论文、文章

要求：
1. 识别 5-20 个实体
2. 每个实体标注类型
3. 按重要性排序
4. 输出格式：JSON 数组

文本内容：
{text[:2000]}

输出示例：
[
  {{"name": "Geoffrey Hinton", "type": "人物"}},
  {{"name": "Google", "type": "组织"}},
  {{"name": "TensorFlow", "type": "工具"}},
  {{"name": "Attention Is All You Need", "type": "论文"}}
]"""

        try:
            response = self._call(model, prompt)
            entities = json.loads(response)
            return entities if isinstance(entities, list) else []
        except Exception:
            return []

    def hyde_enhance(self, query: str) -> str:
        """HyDE 查询增强：生成假设文档"""
        models = CONFIG["ollama"]["models"]
        model = models.get("hyde_enhancement", "gemma4:e2b")

        prompt = f"""用户有一个模糊的想法或问题。请生成一个假设性的文档，这个文档应该能够回答用户的问题。

要求：
1. 文档应该包含用户查询的核心概念
2. 文档应该详细、准确、有条理
3. 使用 Markdown 格式
4. 长度控制在 300-800 字

用户查询：
{query}

生成假设文档："""

        return self._call(model, prompt)

    def analyze_hotwords(self, pages_data: str) -> Dict[str, Any]:
        """分析热词趋势"""
        models = CONFIG["ollama"]["models"]
        model = models.get("hotword_maintenance", "Qwen3.5:4b")

        prompt = f"""你是一个知识库热词分析专家。请分析以下数据，识别热门趋势。

输入数据：
{pages_data[:3000]}

任务：
1. 计算每个页面的热度分数
2. 识别最近 7 天的热词（热度增长 >0.3）
3. 识别长期热门词（热度 >0.7，持续 30 天）
4. 识别新兴概念（首次出现，热度 >0.4）

输出格式：JSON
{{
  "hot_words": [
    {{"word": "transformer", "hotness": 0.85, "trend": "rising"}},
    {{"word": "attention", "hotness": 0.72, "trend": "stable"}}
  ],
  "emerging_concepts": [
    {{"word": "mamba", "hotness": 0.45, "first_seen": "2024-01-15"}}
  ],
  "declining_words": [
    {{"word": "RNN", "hotness": 0.15, "trend": "falling"}}
  ]
}}"""

        try:
            response = self._call(model, prompt)
            return json.loads(response)
        except Exception:
            return {"hot_words": [], "emerging_concepts": [], "declining_words": []}


# ── Desensitization ───────────────────────────────────────────────────
def desensitize(text: str) -> str:
    """去敏处理：移除或替换敏感信息"""
    patterns = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.com'),
        (r'\b\d{3}-\d{4}-\d{4}\b', '***-****-****'),
        (r'\bsk-[a-zA-Z0-9]{20,}\b', 'sk-***'),
        (r'\b\d{4}-\d{4}-\d{4}-\d{4}\b', '****-****-****-****'),
        (r'password\s*[:=]\s*\S+', 'password: ***'),
        (r'api_key\s*[:=]\s*\S+', 'api_key: ***'),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# ── BM25 Search ─────────────────────────────────────────────────────
class BM25:
    """Simple BM25 implementation for markdown search."""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.docs: List[Tuple[str, List[str]]] = []
        self.avgdl = 0
        self.idf: Dict[str, float] = {}
        self.N = 0

    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r'[#*_`~\[\]()>|-]', ' ', text)
        tokens = []
        for word in re.findall(r'[一-鿿]+|[a-z0-9]+', text):
            if len(word) > 1:
                tokens.append(word)
        return tokens

    def add_document(self, path: str, content: str):
        tokens = self.tokenize(content)
        self.docs.append((path, tokens))

    def build_index(self):
        self.N = len(self.docs)
        if self.N == 0:
            return
        total_len = sum(len(tokens) for _, tokens in self.docs)
        self.avgdl = total_len / self.N
        df = Counter()
        for _, tokens in self.docs:
            df.update(set(tokens))
        self.idf = {
            term: math.log((self.N - freq + 0.5) / (freq + 0.5) + 1.0)
            for term, freq in df.items()
        }

    def score(self, query: str, doc_idx: int) -> float:
        query_tokens = self.tokenize(query)
        _, doc_tokens = self.docs[doc_idx]
        doc_len = len(doc_tokens)
        score = 0.0
        for term in query_tokens:
            if term not in self.idf:
                continue
            tf = doc_tokens.count(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += self.idf[term] * numerator / denominator
        return score

    def search(self, query: str, top_k: int = 10, boost_terms: List[str] = None) -> List[Tuple[str, float]]:
        if not self.docs:
            return []
        results = []
        for i in range(len(self.docs)):
            s = self.score(query, i)
            if boost_terms:
                _, tokens = self.docs[i]
                token_set = set(tokens)
                boost = sum(1.5 for t in boost_terms if t.lower() in token_set)
                s *= (1 + boost * 0.3)
            if s > 0:
                results.append((self.docs[i][0], s))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


def load_hot_words(top_k: int = 5) -> List[str]:
    if not HOT_FILE.exists():
        return []
    try:
        data = json.loads(HOT_FILE.read_text())
        concepts = data.get("concepts", {})
        ranked = sorted(
            concepts.items(),
            key=lambda x: x[1].get("heat", 0) * x[1].get("count", 0),
            reverse=True,
        )
        return [name for name, _ in ranked[:top_k]]
    except (json.JSONDecodeError, KeyError):
        return []


# ── Preprocess Command ────────────────────────────────────────────────
def cmd_preprocess(args):
    """Ollama 预处理：关键词提取 + 实体识别 + 去敏"""
    text = args.text
    if not text:
        print(json.dumps({"error": "请提供要预处理的文本"}))
        return

    ollama = OllamaClient()

    result = {
        "original_length": len(text),
        "keywords": [],
        "entities": [],
        "desensitized": False,
        "ollama_available": ollama.is_available(),
    }

    if not result["ollama_available"]:
        print(json.dumps({
            **result,
            "warning": "Ollama 服务不可用，请确保 ollama serve 正在运行。将回退到本地规则处理。"
        }, ensure_ascii=False, indent=2))
        # Fallback: extract keywords via regex
        words = re.findall(r'[一-鿿]{2,}|[a-zA-Z]{3,}', text)
        word_counts = Counter(words)
        result["keywords"] = [w for w, _ in word_counts.most_common(15)]
    else:
        # Parallel would be ideal, but sequential is simpler and avoids threading issues
        result["keywords"] = ollama.extract_keywords(text)
        result["entities"] = ollama.extract_entities(text)

    # Desensitize
    if CONFIG["preprocessing"].get("enable_desensitization", True):
        desensitized = desensitize(text)
        result["desensitized"] = desensitized != text
        result["desensitized_text"] = desensitized[:500] + ("..." if len(desensitized) > 500 else "")

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ── Search Command ────────────────────────────────────────────────────
def cmd_search(args):
    bm25 = BM25()
    md_files = list(WIKI_DIR.rglob("*.md"))
    if not md_files:
        print("[]")
        return
    for f in md_files:
        try:
            content = f.read_text(encoding="utf-8")
            bm25.add_document(str(f.relative_to(VAULT)), content)
        except Exception:
            continue
    bm25.build_index()
    hot_words = load_hot_words(5)
    results = bm25.search(args.query, top_k=getattr(args, 'top_k', 10), boost_terms=hot_words)
    output = [{"path": path, "score": round(score, 4)} for path, score in results]
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ── Sync Command ──────────────────────────────────────────────────────
def cmd_sync(args):
    state = {}
    if SYNC_STATE.exists():
        try:
            state = json.loads(SYNC_STATE.read_text())
        except json.JSONDecodeError:
            state = {}
    files_state = state.get("files", {})
    updated = 0
    added = 0
    removed = 0
    all_current = set()
    for scan_dir in [WIKI_DIR, SOURCES_DIR]:
        if not scan_dir.exists():
            continue
        for f in scan_dir.rglob("*.md"):
            rel = str(f.relative_to(VAULT))
            all_current.add(rel)
            try:
                content = f.read_text(encoding="utf-8")
                sha = hashlib.sha256(content.encode()).hexdigest()
                mtime = f.stat().st_mtime
            except Exception:
                continue
            if rel in files_state:
                if files_state[rel].get("sha256") != sha:
                    files_state[rel] = {"sha256": sha, "mtime": mtime, "updated": datetime.now().isoformat()}
                    updated += 1
            else:
                files_state[rel] = {"sha256": sha, "mtime": mtime, "added": datetime.now().isoformat()}
                added += 1
    for rel in list(files_state.keys()):
        if rel not in all_current and (rel.startswith("wiki/") or rel.startswith("sources/")):
            del files_state[rel]
            removed += 1
    state["files"] = files_state
    state["last_sync"] = datetime.now().isoformat()
    state["stats"] = {
        "total_files": len(files_state),
        "wiki_files": sum(1 for k in files_state if k.startswith("wiki/")),
        "source_files": sum(1 for k in files_state if k.startswith("sources/")),
    }
    SYNC_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"status": "ok", "added": added, "updated": updated, "removed": removed}
    print(json.dumps(result))


# ── Graph Command ─────────────────────────────────────────────────────
def cmd_graph(args):
    links_out = defaultdict(set)
    links_in = defaultdict(set)
    all_pages: Dict[str, dict] = {}
    for f in WIKI_DIR.rglob("*.md"):
        rel = str(f.relative_to(VAULT)).replace("\\", "/")
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = {}
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                fm_text = content[3:end]
                for line in fm_text.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fm[k.strip()] = v.strip()
        all_pages[rel] = {"title": fm.get("title", f.stem), "tags": fm.get("tags", ""),
                          "confidence": fm.get("confidence", "")}
        all_pages[f.stem] = all_pages[rel]
    for f in WIKI_DIR.rglob("*.md"):
        rel = str(f.relative_to(VAULT)).replace("\\", "/")
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in re.finditer(r'\[\[([^\]|#]+)', content):
            target = match.group(1).strip()
            resolved = target
            if target not in all_pages:
                if target + ".md" in all_pages:
                    resolved = target + ".md"
                elif not target.startswith("wiki/") and "wiki/" + target + ".md" in all_pages:
                    resolved = "wiki/" + target + ".md"
                else:
                    stem = target.split("/")[-1] if "/" in target else target
                    for page_path in all_pages:
                        if page_path.endswith("/" + stem + ".md") or page_path == stem + ".md":
                            resolved = page_path
                            break
            links_out[rel].add(resolved)
            links_in[resolved].add(rel)
    all_linked = set(links_out.keys()) | set(links_in.keys())
    orphans = [p for p in all_pages if p not in links_in or len(links_in[p]) == 0]
    orphans = [p for p in orphans if not p.endswith("_README.md") and not p.endswith("sortspec.md")
               and not p.startswith("_README") and not p == "sortspec"]
    hubs = sorted(links_out.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    wanted = [t for t in links_in if t not in all_pages]
    visited = set()
    communities = []
    for page in all_pages:
        if page in visited:
            continue
        queue = [page]
        community = []
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            community.append(node)
            for neighbor in links_out.get(node, set()):
                if neighbor in all_pages:
                    queue.append(neighbor)
            for neighbor in links_in.get(node, set()):
                if neighbor in all_pages:
                    queue.append(neighbor)
        if len(community) >= 3:
            communities.append({"size": len(community), "members": community})
    communities.sort(key=lambda x: x["size"], reverse=True)
    result = {
        "total_pages": len(all_pages),
        "total_links": sum(len(v) for v in links_out.values()),
        "orphans": orphans[:20],
        "hubs": [{"page": p, "links": len(c)} for p, c in hubs],
        "wanted_pages": wanted[:20],
        "communities": communities[:10],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ── Status Command ────────────────────────────────────────────────────
def cmd_status(args):
    wiki_files = list(WIKI_DIR.rglob("*.md")) if WIKI_DIR.exists() else []
    source_files = list(SOURCES_DIR.rglob("*.md")) if SOURCES_DIR.exists() else []
    type_counts = Counter()
    confidence_sum = 0.0
    confidence_count = 0
    low_confidence = []
    missing_frontmatter = []
    for f in wiki_files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if not content.startswith("---"):
            missing_frontmatter.append(str(f.relative_to(VAULT)))
            continue
        end = content.find("---", 3)
        if end < 0:
            missing_frontmatter.append(str(f.relative_to(VAULT)))
            continue
        fm_text = content[3:end]
        fm = {}
        for line in fm_text.split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        tags = fm.get("tags", "")
        if tags:
            first_tag = tags.strip("[]").split(",")[0].strip()
            type_counts[first_tag] += 1
        conf_str = fm.get("confidence", "")
        if conf_str:
            try:
                c = float(conf_str)
                confidence_sum += c
                confidence_count += 1
                if c < 0.7:
                    low_confidence.append(str(f.relative_to(VAULT)))
            except ValueError:
                pass
    avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0.0
    hot_summary = {}
    if HOT_FILE.exists():
        try:
            hot_data = json.loads(HOT_FILE.read_text())
            concepts = hot_data.get("concepts", {})
            top_hot = sorted(concepts.items(), key=lambda x: x[1].get("heat", 0), reverse=True)[:10]
            hot_summary = {name: round(info.get("heat", 0), 3) for name, info in top_hot}
        except (json.JSONDecodeError, KeyError):
            pass
    result = {
        "wiki_pages": len(wiki_files),
        "source_files": len(source_files),
        "by_type": dict(type_counts),
        "avg_confidence": round(avg_confidence, 3),
        "low_confidence_pages": low_confidence[:10],
        "missing_frontmatter": missing_frontmatter[:10],
        "hot_concepts": hot_summary,
        "last_sync": _get_last_sync(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _get_last_sync() -> str:
    if SYNC_STATE.exists():
        try:
            return json.loads(SYNC_STATE.read_text()).get("last_sync", "never")
        except Exception:
            pass
    return "never"


# ── Hot Words Engine ──────────────────────────────────────────────────
HOT_WINDOW_SIZE = 20
HOT_DECAY_RATE = 0.98
HOT_MIN_HEAT = 0.1


def cmd_hot_collect():
    """阶段 1: 收集热词数据"""
    pages_data = []
    if not WIKI_DIR.exists():
        print(json.dumps({"status": "ok", "pages": []}))
        return pages_data

    for f in WIKI_DIR.rglob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = str(f.relative_to(WIKI_DIR))
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        updated_match = re.search(r'updated:\s*(\d{4}-\d{2}-\d{2})', content)
        updated = updated_match.group(1) if updated_match else ""
        pages_data.append({
            "path": rel,
            "title": f.stem,
            "link_count": len(links),
            "updated": updated,
        })

    result = {"status": "ok", "pages_collected": len(pages_data), "pages": pages_data}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return pages_data


def cmd_hot_analyze(pages_data: List[Dict] = None):
    """阶段 2: Ollama 分析热词趋势"""
    if pages_data is None:
        pages_data = cmd_hot_collect()

    ollama = OllamaClient()
    if not ollama.is_available():
        print(json.dumps({
            "status": "fallback",
            "message": "Ollama 不可用，使用本地规则分析",
            "hot_words": [],
            "emerging_concepts": [],
            "declining_words": [],
        }))
        return {"hot_words": [], "emerging_concepts": [], "declining_words": []}

    pages_json = json.dumps(pages_data, ensure_ascii=False, indent=2)
    analysis = ollama.analyze_hotwords(pages_json)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    return analysis


def cmd_hot_update():
    """阶段 3: 更新热词（含数据收集、衰减应用、Ollama 分析）"""
    # Collect
    log_file = VAULT / "log.md"
    concepts_found = Counter()
    if log_file.exists():
        try:
            log_text = log_file.read_text(encoding="utf-8")
        except Exception:
            log_text = ""
        for match in re.finditer(r'\[\[([^\]|#]+)', log_text):
            concepts_found[match.group(1).strip().lower()] += 1

    # Load existing
    hot_data = {"concepts": {}, "updated": datetime.now().isoformat(), "window_size": HOT_WINDOW_SIZE}
    if HOT_FILE.exists():
        try:
            hot_data = json.loads(HOT_FILE.read_text())
        except json.JSONDecodeError:
            pass

    concepts = hot_data.get("concepts", {})

    # Apply time decay
    last_updated = hot_data.get("updated", "")
    if last_updated:
        try:
            last_dt = datetime.fromisoformat(last_updated)
            days_passed = (datetime.now() - last_dt).total_seconds() / 86400
            decay = HOT_DECAY_RATE ** days_passed
            for name in list(concepts.keys()):
                concepts[name]["heat"] = concepts[name].get("heat", 0) * decay
                if concepts[name]["heat"] < HOT_MIN_HEAT:
                    del concepts[name]
        except (ValueError, TypeError):
            pass

    # Update with new mentions
    for concept, count in concepts_found.items():
        if concept in concepts:
            concepts[concept]["count"] = concepts[concept].get("count", 0) + count
            concepts[concept]["heat"] = min(1.0, concepts[concept].get("heat", 0) + count * 0.05)
        else:
            concepts[concept] = {
                "count": count,
                "heat": min(1.0, count * 0.05),
                "first_seen": datetime.now().isoformat(),
            }

    # Try Ollama-enhanced analysis
    try:
        pages_data = cmd_hot_collect()
        ollama = OllamaClient()
        if ollama.is_available():
            pages_json = json.dumps(pages_data, ensure_ascii=False, indent=2)
            oa = ollama.analyze_hotwords(pages_json)
            # Merge Ollama insights into concepts
            for hw in oa.get("hot_words", []):
                name = hw.get("word", "").lower()
                if name and name in concepts:
                    concepts[name]["ollama_trend"] = hw.get("trend", "stable")
                    concepts[name]["ollama_hotness"] = hw.get("hotness", 0)
    except Exception:
        pass  # Silently fall back to rule-based

    hot_data["concepts"] = concepts
    hot_data["updated"] = datetime.now().isoformat()
    HOT_FILE.write_text(json.dumps(hot_data, ensure_ascii=False, indent=2), encoding="utf-8")

    updated_pages = _sync_hotness_to_pages(concepts)
    _generate_heat_report(concepts)

    print(json.dumps({
        "status": "ok",
        "concepts_tracked": len(concepts),
        "pages_updated": updated_pages,
    }))


def cmd_hot_report():
    """阶段 4: 生成热词报告"""
    if not HOT_FILE.exists():
        print("# Heat Report\n\nNo hot concepts data yet.")
        return
    try:
        hot_data = json.loads(HOT_FILE.read_text())
    except json.JSONDecodeError:
        print("# Heat Report\n\nCorrupted data file.")
        return

    concepts = hot_data.get("concepts", {})
    ranked = sorted(concepts.items(), key=lambda x: x[1].get("heat", 0), reverse=True)

    report = [
        f"# Heat Report — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"Tracking {len(concepts)} concepts (decay: {HOT_DECAY_RATE}/day, min: {HOT_MIN_HEAT})",
        "",
        "## 🔥 Top Hot Concepts",
        "",
        "| Rank | Concept | Heat | Mentions | Trend |",
        "|------|---------|------|----------|-------|",
    ]

    for i, (name, info) in enumerate(ranked[:20], 1):
        heat = info.get("heat", 0)
        count = info.get("count", 0)
        ollama_trend = info.get("ollama_trend", "")
        if ollama_trend == "rising":
            trend = "↗️"
        elif ollama_trend == "falling":
            trend = "↘️"
        elif heat > 0.7:
            trend = "🔥"
        elif heat > 0.4:
            trend = "📈"
        elif heat > 0.2:
            trend = "📊"
        else:
            trend = "📉"
        report.append(f"| {i} | [[{name}]] | {heat:.3f} | {count} | {trend} |")

    report.extend(["", "## 📉 Cooling Concepts", ""])
    cooling = [x for x in ranked if x[1].get("heat", 0) < 0.2]
    if cooling:
        for name, info in cooling[:10]:
            report.append(f"- [[{name}]] — heat: {info.get('heat', 0):.3f}")
    else:
        report.append("No concepts below cooling threshold.")

    # Emerging concepts (from Ollama analysis or first_seen)
    emerging = [x for x in ranked if x[1].get("first_seen") and x[1].get("heat", 0) > 0.3]
    if emerging:
        report.extend(["", "## 🌱 Emerging Concepts", ""])
        for name, info in emerging[:10]:
            first_seen = info.get("first_seen", "")[:10]
            report.append(f"- **{name}** (热度: {info.get('heat', 0):.2f}, 首次出现: {first_seen})")

    report_text = "\n".join(report)
    try:
        print(report_text)
    except UnicodeEncodeError:
        safe = report_text.encode('gbk', errors='replace').decode('gbk')
        print(safe)

    heat_report_path = SYSTEM_DIR / "Heat Report.md"
    heat_report_path.write_text(report_text, encoding="utf-8")


def cmd_hot(args):
    """Hot words router: dispatches to collect / analyze / update / report."""
    action = getattr(args, 'action', 'report')
    if action == "collect":
        cmd_hot_collect()
    elif action == "analyze":
        pages_data = cmd_hot_collect()
        cmd_hot_analyze(pages_data)
    elif action == "update":
        cmd_hot_update()
    elif action == "report":
        cmd_hot_report()


def _generate_heat_report(concepts: dict):
    """Generate Heat Report.md from hot concepts data."""
    ranked = sorted(concepts.items(), key=lambda x: x[1].get("heat", 0), reverse=True)
    report = [
        f"# Heat Report — {datetime.now().strftime('%Y-W%U')}",
        "",
        f"Tracking {len(concepts)} concepts",
        "",
        "## Top 20 热词",
        "| 排名 | 热词 | 热度 | 趋势 |",
        "|------|------|------|------|",
    ]
    for i, (word, info) in enumerate(ranked[:20], 1):
        trend = info.get("ollama_trend", "→")
        trend_icon = {"rising": "↗️", "stable": "→", "falling": "↘️"}.get(trend, "→")
        report.append(f"| {i} | {word} | {info.get('heat', 0):.2f} | {trend_icon} |")

    report.extend(["", "## 本周新兴概念", ""])
    emerging = [(n, i) for n, i in ranked if i.get("first_seen") and i.get("heat", 0) > 0.3]
    if emerging:
        for name, info in emerging[:10]:
            first_seen = info.get("first_seen", "")[:10]
            report.append(f"- **{name}** (热度: {info.get('heat', 0):.2f}, 首次出现: {first_seen})")
    else:
        report.append("暂无新兴概念。")

    report.extend(["", "## 本周暴跌热词", ""])
    declining = [(n, i) for n, i in ranked if i.get("ollama_trend") == "falling"]
    if declining:
        for name, info in declining[:10]:
            report.append(f"- **{name}** (热度: {info.get('heat', 0):.2f})")
    else:
        report.append("暂无暴跌热词。")

    (SYSTEM_DIR / "Heat Report.md").write_text("\n".join(report), encoding="utf-8")


def _compute_hotness(page_path: str, backlinks_count: int,
                     days_since_edit: int, concept_heat: float) -> float:
    citation_score = min(1.0, backlinks_count / 10.0)
    recency_score = max(0.0, 1.0 - days_since_edit / 90.0)
    trend_score = concept_heat
    return citation_score * 0.6 + recency_score * 0.2 + trend_score * 0.2


def _sync_hotness_to_pages(concepts: dict) -> int:
    if not WIKI_DIR.exists():
        return 0
    updated = 0
    for f in WIKI_DIR.rglob("*.md"):
        page_slug = f.stem.lower()
        concept_info = concepts.get(page_slug, {})
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = _parse_frontmatter(content)
        hotness_str = fm.get("hotness", "0")
        try:
            current_hotness = float(hotness_str)
        except (ValueError, TypeError):
            current_hotness = 0.0
        updated_str = fm.get("updated", "")
        days_since = 30
        if updated_str:
            try:
                dt = datetime.strptime(updated_str.strip(), "%Y-%m-%d")
                days_since = (datetime.now() - dt).days
            except ValueError:
                pass
        backlinks = 0
        page_name = f.stem
        for other in WIKI_DIR.rglob("*.md"):
            if other == f:
                continue
            try:
                other_content = other.read_text(encoding="utf-8")
                if f"[[{page_name}]]" in other_content or f"[[{page_name}|" in other_content:
                    backlinks += 1
            except Exception:
                pass
        concept_heat = concept_info.get("heat", 0)
        new_hotness = _compute_hotness(str(f), backlinks, days_since, concept_heat)
        new_hotness = current_hotness * 0.98 * 0.5 + new_hotness * 0.5
        if abs(new_hotness - current_hotness) > 0.01:
            _update_frontmatter_field(f, "hotness", f"{new_hotness:.3f}")
            updated += 1
    return updated


# ── HyDE Command ─────────────────────────────────────────────────────
def cmd_hyde(args):
    """Generate a hypothetical document from a fuzzy idea for query expansion.

    Uses Ollama (gemma4:e2b) if available, otherwise saves the prompt template
    for manual LLM processing.
    """
    idea = args.idea
    ollama = OllamaClient()

    if ollama.is_available() and CONFIG["preprocessing"].get("enable_hyde", True):
        try:
            hyde_doc = ollama.hyde_enhance(idea)
            hyde_file = STATE_DIR / "hyde_doc.md"
            hyde_file.write_text(hyde_doc, encoding="utf-8")
            result = {
                "status": "ok",
                "source": "ollama",
                "model": CONFIG["ollama"]["models"].get("hyde_enhancement", "gemma4:e2b"),
                "hypothetical_doc": hyde_doc[:500],
                "saved_to": str(hyde_file),
                "instructions": "Use this hypothetical document as a search query against the wiki."
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        except Exception:
            pass  # Fall through to manual prompt

    # Manual fallback
    prompt = f"""You are a knowledge synthesis engine. Given a fuzzy idea, generate a short
hypothetical document (3-5 sentences) that describes what an ideal wiki page about
this topic would contain. Use technical, precise language. Include possible
aliases, related concepts, and key claims.

Idea: {idea}

Hypothetical Document:"""

    hyde_file = STATE_DIR / "hyde_prompt.txt"
    hyde_file.write_text(prompt, encoding="utf-8")

    result = {
        "status": "ok",
        "source": "manual",
        "prompt_saved": str(hyde_file),
        "instructions": "Feed this prompt to the LLM, then save the response to .llm-wiki/hyde_doc.md and re-run search with --hyde flag."
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ── Content Decay — Five-Tier System ─────────────────────────────────
DECAY_TIERS = [
    (0.7, 30, 0.80, "L1", True),
    (0.5, 45, 0.60, "L2", True),
    (0.3, 60, 0.40, "L3", False),
    (0.2, 75, 0.20, "L4", False),
    (0.15, 90, 0.10, "L5", False),
]


def cmd_decay(args):
    auto_only = getattr(args, 'auto', False)
    if not HOT_FILE.exists():
        print(json.dumps({"status": "no_hot_data"}))
        return
    try:
        hot_data = json.loads(HOT_FILE.read_text())
    except json.JSONDecodeError:
        print(json.dumps({"status": "error"}))
        return
    concepts = hot_data.get("concepts", {})
    archive_dir = SYSTEM_DIR / "Archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    auto_results = []
    review_queue = []
    review_file = SYSTEM_DIR / "Review Queue.md"
    for f in WIKI_DIR.rglob("*.md"):
        rel = str(f.relative_to(VAULT))
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = _parse_frontmatter(content)
        hotness_str = fm.get("hotness", "0")
        try:
            hotness = float(hotness_str)
        except (ValueError, TypeError):
            hotness = 0.0
        updated_str = fm.get("updated", "")
        days_stale = 999
        if updated_str:
            try:
                updated_dt = datetime.strptime(updated_str.strip(), "%Y-%m-%d")
                days_stale = (datetime.now() - updated_dt).days
            except ValueError:
                pass
        applicable_tier = None
        for hot_max, stale_min, retention, tier_name, is_auto in DECAY_TIERS:
            if hotness < hot_max and days_stale >= stale_min:
                applicable_tier = (retention, tier_name, is_auto)
            else:
                break
        if applicable_tier is None:
            continue
        retention, tier_name, is_auto = applicable_tier
        if auto_only and not is_auto:
            continue
        reduced = _reduce_content(content, retention)
        if is_auto or (auto_only and is_auto):
            archive_path = archive_dir / f"{tier_name}-{f.name}"
            archive_path.write_text(reduced, encoding="utf-8")
            _update_frontmatter_field(f, "hotness", f"{hotness:.3f}")
            _update_frontmatter_field(f, "decay_tier", tier_name)
            auto_results.append({
                "page": rel,
                "tier": tier_name,
                "hotness": round(hotness, 3),
                "days_stale": days_stale,
                "retention": f"{int(retention * 100)}%",
                "archived_to": str(archive_path.relative_to(VAULT)),
                "auto_applied": True,
            })
        else:
            review_queue.append({
                "page": rel,
                "tier": tier_name,
                "hotness": round(hotness, 3),
                "days_stale": days_stale,
                "retention": f"{int(retention * 100)}%",
                "candidate_path": str((archive_dir / f"{tier_name}-{f.name}").relative_to(VAULT)),
            })
    if review_queue:
        rq_lines = []
        if review_file.exists():
            rq_lines = review_file.read_text(encoding="utf-8").split("\n")
        else:
            rq_lines = ["# Review Queue", "", "待人工确认的操作：", ""]
        for item in review_queue:
            rq_lines.append(
                f"- [ ] [[{item['page'].replace('wiki/', '').replace('.md', '')}]] "
                f"— {item['tier']} 衰减 ({item['retention']}) | "
                f"hotness: {item['hotness']} | "
                f"stale: {item['days_stale']}d | "
                f"候选: {item['candidate_path']}"
            )
        review_file.write_text("\n".join(rq_lines) + "\n", encoding="utf-8")
    result = {
        "status": "ok",
        "auto_applied": len(auto_results),
        "queued_for_review": len(review_queue),
        "auto_items": auto_results,
        "review_items": review_queue,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _reduce_content(content: str, retention: float) -> str:
    lines = content.split("\n")
    if retention >= 0.6:
        return content
    elif retention >= 0.4:
        kept = []
        for line in lines:
            if line.startswith("#") or line.startswith("---") or ":" in line[:30]:
                kept.append(line)
            elif kept and kept[-1] == "" and line.strip():
                kept.append(line[:200] + "...")
                kept.append("")
        return "\n".join(kept)
    else:
        kept = []
        in_frontmatter = False
        for line in lines:
            if line.startswith("---"):
                in_frontmatter = not in_frontmatter
                kept.append(line)
                continue
            if in_frontmatter:
                kept.append(line)
            elif line.startswith("#") and not in_frontmatter:
                kept.append(line)
                break
        kept.append(f"\n*[Content archived — heat: {retention:.0%}]*")
        kept.append(f"\n**Keywords preserved for search indexing.**")
        return "\n".join(kept)


def _parse_frontmatter(content: str) -> dict:
    fm = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            for line in content[3:end].split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
    return fm


def _update_frontmatter_field(filepath: Path, field: str, value: str):
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return
    if not content.startswith("---"):
        return
    end = content.find("---", 3)
    if end < 0:
        return
    fm_text = content[3:end]
    lines = fm_text.split("\n")
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{field}:"):
            new_lines.append(f"{field}: {value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{field}: {value}")
    new_content = "---\n" + "\n".join(new_lines) + "\n" + content[end:]
    filepath.write_text(new_content, encoding="utf-8")


# ── Index Rebuild ─────────────────────────────────────────────────────
def cmd_index(args):
    index = {"pages": [], "generated": datetime.now().isoformat()}
    for f in sorted(WIKI_DIR.rglob("*.md")):
        rel = str(f.relative_to(VAULT))
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = {}
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                for line in content[3:end].split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fm[k.strip()] = v.strip()
        page_type = fm.get("type", "")
        if not page_type:
            tags_str = fm.get("tags", "")
            if tags_str:
                page_type = tags_str.strip("[]").split(",")[0].strip()
        index["pages"].append({
            "path": rel,
            "title": fm.get("title", f.stem),
            "type": page_type,
            "tags": fm.get("tags", ""),
            "description": fm.get("description", ""),
            "updated": fm.get("updated", ""),
            "confidence": fm.get("confidence", ""),
        })
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    index_md = [
        f"# Wiki Index — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"Total pages: {len(index['pages'])}",
        "",
    ]
    by_type = defaultdict(list)
    for p in index["pages"]:
        by_type[p["type"] or "uncategorized"].append(p)
    for ptype in ["entity", "concept", "summary", "synthesis", "query", "uncategorized"]:
        pages = by_type.get(ptype, [])
        if pages:
            index_md.append(f"## {ptype.title()} ({len(pages)})")
            index_md.append("")
            for p in sorted(pages, key=lambda x: x["title"]):
                desc = p.get("description", "")
                conf = p.get("confidence", "")
                flags = ""
                if conf:
                    try:
                        if float(conf) < 0.7:
                            flags = " #review"
                    except ValueError:
                        pass
                index_md.append(f"- [[{p['title']}]] — {desc}{flags}")
            index_md.append("")
    (VAULT / "index.md").write_text("\n".join(index_md), encoding="utf-8")
    print(json.dumps({"status": "ok", "pages_indexed": len(index["pages"])}))


# ── CLI Entry Point ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LLM Wiki CLI v2.0 — 知识编译引擎")
    subparsers = parser.add_subparsers(dest="command")

    # preprocess
    p = subparsers.add_parser("preprocess", help="Ollama 预处理：关键词提取 + 实体识别 + 去敏")
    p.add_argument("text", help="要预处理的文本")

    # search
    p = subparsers.add_parser("search", help="BM25 搜索 Wiki")
    p.add_argument("query", help="搜索查询")
    p.add_argument("-k", "--top-k", type=int, default=10)

    # hyde
    p = subparsers.add_parser("hyde", help="生成 HyDE 查询增强（优先使用 Ollama）")
    p.add_argument("idea", help="模糊想法")

    # sync
    subparsers.add_parser("sync", help="同步文件索引")

    # graph
    subparsers.add_parser("graph", help="链接图谱分析")

    # status
    subparsers.add_parser("status", help="Vault 统计与健康摘要")

    # hot (with subcommands)
    p = subparsers.add_parser("hot", help="热词引擎")
    p.add_argument("action", nargs="?", default="report",
                   choices=["collect", "analyze", "update", "report"],
                   help="collect / analyze / update / report")

    # decay
    p = subparsers.add_parser("decay", help="内容衰减处理")
    p.add_argument("--auto", action="store_true", help="仅自动执行 L1-L2 层级")

    # index
    subparsers.add_parser("index", help="重建全库索引")

    args = parser.parse_args()

    if args.command == "preprocess":
        cmd_preprocess(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "hyde":
        cmd_hyde(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "graph":
        cmd_graph(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "hot":
        cmd_hot(args)
    elif args.command == "decay":
        cmd_decay(args)
    elif args.command == "index":
        cmd_index(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
