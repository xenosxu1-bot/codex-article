# -*- coding: utf-8 -*-
"""文章事实、版权与安全边界扫描。

本脚本不再把标题、章节、标点、代码块、表格、图片数量或视觉风格当成硬规则。
只阻断可确认的文件完整性、敏感信息和本地引用问题；事实与版权风险输出人工核验提醒。
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
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

METADATA_DIR = ROOT / "07-资料与流程" / "03-资产与核验" / "文章元数据"
PREPUBLICATION_MARKERS = ("draft", "reviewing", "s1", "s2", "s3", "s4", "s5", "初稿", "待质检", "待发布")
EDITORIAL_GENERIC_RE = re.compile(r"(?:^|[。！？\n])\s*(?:本文将|本文主要|在当今|随着.{0,20}(?:发展|普及)|首先，|其次，|最后，)")
EDITORIAL_CLAIM_RE = re.compile(r"(?:不是.{0,35}而是|真正.{0,20}(?:是|在于)|关键在于|核心是|本质上)")
EDITORIAL_BOUNDARY_RE = re.compile(r"(?:但|不过|然而|边界|风险|代价|失败|误区|不适合|不能|不可|回滚|限制)")
EDITORIAL_ACTION_RE = re.compile(r"(?:清单|步骤|任务卡|检查|试验|模板|决策树|流程|对照|可以这样做|第一步)")
REQUIRED_BRIEF_FIELDS = (
    "reader_moment",
    "emotional_tension",
    "contrarian_claim",
    "share_target",
    "reusable_asset",
    "counterexample",
    "figure_plan",
)


def iter_articles():
    """Yield legacy flat articles and article-package bodies without treating package assets as articles."""
    for directory in sorted(p for p in ROOT.iterdir() if p.is_dir() and ARTICLE_DIR_RE.match(p.name)):
        for file in sorted(directory.rglob("*.md")):
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


def load_metadata(path: Path):
    target = path.relative_to(ROOT).as_posix()
    if not METADATA_DIR.exists():
        return None
    for metadata_path in METADATA_DIR.glob("*.json"):
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        article_path = str(data.get("article", {}).get("path", "")).replace("\\", "/")
        if article_path == target:
            return data
    return None


def is_prepublication(metadata) -> bool:
    if not metadata:
        return False
    status = str(metadata.get("article", {}).get("status", "")).lower()
    return any(marker in status for marker in PREPUBLICATION_MARKERS)


def editorial_warnings(text: str, metadata) -> list[str]:
    warnings = []
    brief = metadata.get("brief", {}) if metadata else {}
    missing = [field for field in REQUIRED_BRIEF_FIELDS if not brief.get(field)]
    if missing:
        warnings.append("首稿 Brief 缺少读者时刻、情绪张力、核心判断、分享对象、可复用资产、反例或配图任务；请补齐后再做总编辑复审")

    first_window = text[:1800]
    if EDITORIAL_GENERIC_RE.search(first_window):
        warnings.append("开头或段落出现模板化导语；请改成具体场景、选择困境或失败路径")
    if not EDITORIAL_CLAIM_RE.search(first_window):
        warnings.append("前 20% 正文暂未发现明确核心判断；请确认文章不是从主题介绍直接展开")
    if not EDITORIAL_BOUNDARY_RE.search(text):
        warnings.append("正文暂未发现反例、代价、风险或不适用边界；请补充内容深度")
    if not EDITORIAL_ACTION_RE.search(text):
        warnings.append("正文暂未发现可复用的清单、任务卡、试验、流程或决策工具；请补充读者行动资产")
    if re.search(r"(?:希望本文能够帮助你|总的来说，|综上所述，)", text):
        warnings.append("结尾或总结出现泛化套话；请改成具体的行动型结论")
    return warnings


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

    metadata = load_metadata(path)
    if is_prepublication(metadata):
        for message in editorial_warnings(text, metadata):
            warnings.append(("P2", message))

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