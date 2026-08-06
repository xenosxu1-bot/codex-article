# -*- coding: utf-8 -*-
"""文章事实、版权与安全边界扫描。

本脚本不再把标题、章节、标点、代码块、表格、图片数量或视觉风格当成硬规则。
只阻断可确认的文件完整性、敏感信息和本地引用问题；事实与版权风险输出人工核验提醒。
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_DIR_RE = re.compile(r"^0[1-6]-")
ARTICLE_FILE_RE = re.compile(r"^\d{2}-.+\.md$")
BAD_CHARS = ["�", "锟", "鐭", "鈥", "Ã", "Â"]
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
SECRET_RE = re.compile(
    r"(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"(?:token|api[_-]?key|secret|password)\s*=\s*['\"][A-Za-z0-9_\-]{12,})",
    re.IGNORECASE,
)
FACT_REVIEW_RE = re.compile(
    r"(?:首次|唯一|行业第一|绝对|保证|100%|提升\s*\d+%|降低\s*\d+%|官方认证|权威认证|客户案例|生产环境)",
    re.IGNORECASE,
)
RIGHTS_REVIEW_RE = re.compile(
    r"(?:转载|截图|Logo|商标|字体|图片来源|许可|授权|版权|开源协议|官方界面|第三方素材)",
    re.IGNORECASE,
)


def iter_articles():
    for directory in sorted(p for p in ROOT.iterdir() if p.is_dir() and ARTICLE_DIR_RE.match(p.name)):
        for file in sorted(directory.glob("*.md")):
            if ARTICLE_FILE_RE.match(file.name):
                yield file


def normalize_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        title_match = re.match(r"([^\s]+)\s+[\"'].*[\"']$", target)
        if title_match:
            target = title_match.group(1)
    return unquote(target.split("#", 1)[0].split("?", 1)[0].strip("<>"))


def scan_file(path: Path):
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    problems: list[tuple[str, str]] = []
    warnings: list[tuple[str, str]] = []

    if any(ch in text for ch in BAD_CHARS):
        problems.append(("P0", "疑似乱码字符，先修复文件编码或内容损坏"))
    if SECRET_RE.search(text):
        problems.append(("P0", "疑似包含密钥、Token、密码或其他敏感凭据"))

    for raw_ref in IMAGE_RE.findall(text):
        normalized = normalize_target(raw_ref)
        if not normalized or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", normalized) or normalized.startswith("//"):
            continue
        target = (path.parent / normalized.replace("/", "\\")).resolve()
        if not target.exists():
            problems.append(("P0", f"正文引用的本地图片不存在：{normalized}"))

    if FACT_REVIEW_RE.search(text):
        warnings.append(("P2", "检测到可能需要来源或事实核验的强表述；不因风格或结构自动阻断"))
    if RIGHTS_REVIEW_RE.search(text):
        warnings.append(("P2", "检测到外部素材、官方界面或版权相关表述；请人工确认来源和许可范围"))

    return rel, problems, warnings


def main():
    total = 0
    counts = {"P0": 0, "P1": 0, "P2": 0}
    for article in iter_articles():
        total += 1
        rel, problems, warnings = scan_file(article)
        if not problems and not warnings:
            continue
        print(f"\n{rel}")
        for level, message in [*problems, *warnings]:
            counts[level] += 1
            print(f"  [{level}] {message}")
    print(f"\n扫描文章：{total} 篇")
    print(f"P0: {counts['P0']}  P1: {counts['P1']}  P2: {counts['P2']}")
    return 1 if counts["P0"] else 0


if __name__ == "__main__":
    sys.exit(main())