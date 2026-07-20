# -*- coding: utf-8 -*-
"""检查文章图片资产与 Markdown 图片引用。

检查范围：
1. 正式文章正文中的 Markdown 图片引用必须指向存在的本地文件。
2. 每篇正式文章建议至少有一个同编号封面文件。
3. 正文插图目录中未被正式文章引用的图片、已下架编号图片只作为 P2 提醒，便于后续清理，不阻断发布。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ASSET_FILE = ROOT / "07-资料与流程" / "文章资产登记表.md"
IMAGE_ROOT = ROOT / "08-素材库" / "图片"
COVER_DIR = IMAGE_ROOT / "文章封面"
INLINE_DIR = IMAGE_ROOT / "正文插图"
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_assets() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in ASSET_FILE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line or "编号" in line:
            continue
        cols = split_row(line)
        if len(cols) < 8 or not cols[0].isdigit():
            continue
        path_match = re.search(r"`([^`]+)`", cols[5])
        rows.append({
            "id": str(int(cols[0])).zfill(2),
            "title": cols[1],
            "path": path_match.group(1) if path_match else cols[5],
            "status": cols[7],
        })
    return rows


def normalize_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        title_match = re.match(r"([^\s]+)\s+[\"'].*[\"']$", target)
        if title_match:
            target = title_match.group(1)
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def resolve_markdown_path(md_file: Path, raw: str) -> Path | None:
    target = normalize_target(raw)
    if not target:
        return None
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("//"):
        return None
    return (md_file.parent / target.replace("/", "\\")).resolve()


def collect_used_images(article_files: list[Path]) -> tuple[set[Path], list[str]]:
    used: set[Path] = set()
    problems: list[str] = []
    for article in article_files:
        text = article.read_text(encoding="utf-8")
        for raw_ref in IMAGE_RE.findall(text):
            target = resolve_markdown_path(article, raw_ref)
            if target is None:
                continue
            used.add(target)
            if not target.exists():
                problems.append(f"[P0] {article.relative_to(ROOT)} 引用的图片不存在：{raw_ref}")
    return used, problems


def main() -> int:
    assets = parse_assets()
    formal_ids = {item["id"] for item in assets}
    article_files = [(ROOT / item["path"]).resolve() for item in assets]

    problems: list[str] = []
    warnings: list[str] = []

    for item, article in zip(assets, article_files):
        if not article.exists():
            problems.append(f"[P0] 资产登记表中的正文不存在：{item['path']}")

    existing_articles = [article for article in article_files if article.exists()]
    used_images, image_ref_problems = collect_used_images(existing_articles)
    problems.extend(image_ref_problems)

    cover_files = [p for p in COVER_DIR.glob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS] if COVER_DIR.exists() else []
    cover_ids = {m.group(1) for p in cover_files if (m := re.match(r"^(\d{2})-", p.name))}
    missing_cover = sorted(formal_ids - cover_ids)
    for no in missing_cover:
        problems.append(f"[P1] 正式文章 {no} 缺少同编号封面文件")

    inline_files = [p for p in INLINE_DIR.glob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS] if INLINE_DIR.exists() else []
    for p in inline_files:
        m = re.match(r"^(\d{2})-", p.name)
        if not m:
            warnings.append(f"[P2] 正文插图未使用编号命名：{p.relative_to(ROOT)}")
            continue
        no = m.group(1)
        if no not in formal_ids:
            warnings.append(f"[P2] 正文插图编号 {no} 不在正式文章登记表中：{p.relative_to(ROOT)}")
        elif p.resolve() not in used_images:
            warnings.append(f"[P2] 正文插图未被正式文章引用：{p.relative_to(ROOT)}")

    print(f"正式文章：{len(assets)} 篇")
    print(f"正文图片引用：{len(used_images)} 个")
    print(f"封面文件：{len(cover_files)} 个；正文插图文件：{len(inline_files)} 个")

    if problems:
        print("\n阻断问题：")
        for item in problems:
            print(item)
    if warnings:
        print("\n提醒项：")
        display_limit = 20
        for item in warnings[:display_limit]:
            print(item)
        if len(warnings) > display_limit:
            print(f"……另有 {len(warnings) - display_limit} 项提醒未显示")

    p0 = sum(1 for item in problems if item.startswith("[P0]"))
    p1 = sum(1 for item in problems if item.startswith("[P1]"))
    p2 = len(warnings)
    print(f"\n图片资产检查：P0={p0} P1={p1} P2={p2}")
    return 1 if p0 or p1 else 0


if __name__ == "__main__":
    sys.exit(main())
