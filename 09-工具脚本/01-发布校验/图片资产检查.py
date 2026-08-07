# -*- coding: utf-8 -*-
"""检查正式文章包中的图片资产、article.json 与 Markdown 图片引用。

正式文章不再依赖顶层集中素材库：封面放在文章包 assets/cover/，
正文插图放在 assets/figures/，不再使用的文章专属文件放在 assets/archive/。
未入库或无法唯一归属的历史文件由 07-资料与流程/03-资产与核验/历史素材归档/ 保留，
不得被正式文章正文直接引用。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
ASSET_FILE = ROOT / "07-资料与流程" / "03-资产与核验" / "文章资产登记表.md"
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}


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
        rows.append(
            {
                "id": str(int(cols[0])).zfill(2),
                "title": cols[1],
                "path": path_match.group(1) if path_match else cols[5],
                "status": cols[7],
            }
        )
    return rows


def normalize_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        title_match = re.match(r"([^\s]+)\s+[\"'].*[\"']$", target)
        if title_match:
            target = title_match.group(1)
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def resolve_markdown_path(md_file: Path, raw: str) -> Path | None:
    target = normalize_target(raw)
    if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("//"):
        return None
    return (md_file.parent / target.replace("/", "\\")).resolve()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def image_files(directory: Path) -> set[Path]:
    if not directory.exists():
        return set()
    return {path.resolve() for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTS}


def manifest_file_paths(value: object, key: str, problems: list[str], article_label: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        problems.append(f"[P0] {article_label} article.json 的 assets.{key} 格式无效。")
        return []
    paths: list[str] = []
    for entry in value:
        file_value = entry.get("file") if isinstance(entry, dict) else entry
        if not isinstance(file_value, str) or not file_value.strip():
            problems.append(f"[P0] {article_label} article.json 的 assets.{key} 缺少 file。")
            continue
        paths.append(file_value.replace("\\", "/"))
    return paths


def check_article(item: dict[str, str]) -> tuple[list[str], list[str], int, int, int]:
    problems: list[str] = []
    warnings: list[str] = []
    cover_count = figure_count = archive_count = 0
    article = (ROOT / item["path"]).resolve()
    label = f"{item['id']} {item['title']}"
    if not article.is_file():
        return [f"[P0] 资产登记表中的正文不存在：{item['path']}"], warnings, 0, 0, 0

    package_dir = article.parent
    manifest_path = package_dir / "article.json"
    assets_root = package_dir / "assets"
    cover_dir = assets_root / "cover"
    figure_dir = assets_root / "figures"
    archive_dir = assets_root / "archive"

    if not manifest_path.is_file():
        return [f"[P0] {relative(article)} 缺少 article.json。"], warnings, 0, 0, 0
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"[P0] {relative(manifest_path)} 无法解析：{exc}"], warnings, 0, 0, 0

    article_meta = manifest.get("article")
    if not isinstance(article_meta, dict):
        problems.append(f"[P0] {relative(manifest_path)} 缺少 article 对象。")
        article_meta = {}
    expected_path = item["path"].replace("\\", "/")
    if article_meta.get("id") != item["id"]:
        problems.append(f"[P0] {relative(manifest_path)} article.id 与资产登记表不一致。")
    if article_meta.get("title") != item["title"]:
        problems.append(f"[P0] {relative(manifest_path)} article.title 与资产登记表不一致。")
    if article_meta.get("path") != expected_path:
        problems.append(f"[P0] {relative(manifest_path)} article.path 与资产登记表不一致。")
    if article_meta.get("category") != package_dir.parent.name:
        problems.append(f"[P0] {relative(manifest_path)} article.category 与文章分类目录不一致。")

    assets = manifest.get("assets")
    if not isinstance(assets, dict):
        problems.append(f"[P0] {relative(manifest_path)} 缺少 assets 对象。")
        assets = {}
    cover_list = manifest_file_paths(assets.get("cover"), "cover", problems, label)
    figure_list = manifest_file_paths(assets.get("figures", []), "figures", problems, label)
    archive_list = manifest_file_paths(assets.get("archived_files", []), "archived_files", problems, label)

    cover_paths = {(package_dir / entry).resolve() for entry in cover_list}
    figure_paths = {(package_dir / entry).resolve() for entry in figure_list}
    archive_paths = {(package_dir / entry).resolve() for entry in archive_list}
    actual_covers = image_files(cover_dir)
    actual_figures = image_files(figure_dir)
    actual_archives = image_files(archive_dir)
    cover_count = len(actual_covers)
    figure_count = len(actual_figures)
    archive_count = len(actual_archives)

    for path in cover_paths:
        if not is_within(path, cover_dir):
            problems.append(f"[P0] {relative(manifest_path)} 的封面必须位于 assets/cover/：{relative(path)}")
        elif not path.is_file():
            problems.append(f"[P0] {relative(manifest_path)} 登记的封面不存在：{relative(path)}")
    for path in figure_paths:
        if not is_within(path, figure_dir):
            problems.append(f"[P0] {relative(manifest_path)} 的正文插图必须位于 assets/figures/：{relative(path)}")
        elif not path.is_file():
            problems.append(f"[P0] {relative(manifest_path)} 登记的正文插图不存在：{relative(path)}")
    for path in archive_paths:
        if not is_within(path, archive_dir):
            problems.append(f"[P0] {relative(manifest_path)} 的历史文件必须位于 assets/archive/：{relative(path)}")
        elif not path.is_file():
            problems.append(f"[P0] {relative(manifest_path)} 登记的历史文件不存在：{relative(path)}")

    if actual_covers != cover_paths:
        for path in sorted(actual_covers - cover_paths):
            warnings.append(f"[P1] {relative(path)} 未登记到 article.json 的 assets.cover。")
        for path in sorted(cover_paths - actual_covers):
            if path.is_file():
                warnings.append(f"[P1] {relative(path)} 的扩展名不属于支持的图片类型。")
    if actual_figures != figure_paths:
        for path in sorted(actual_figures - figure_paths):
            warnings.append(f"[P1] {relative(path)} 未登记到 article.json 的 assets.figures。")
    if actual_archives != archive_paths:
        for path in sorted(actual_archives - archive_paths):
            warnings.append(f"[P1] {relative(path)} 未登记到 article.json 的 assets.archived_files。")

    used_figures: set[Path] = set()
    for raw_ref in IMAGE_RE.findall(article.read_text(encoding="utf-8")):
        target = resolve_markdown_path(article, raw_ref)
        if target is None:
            continue
        if not target.exists():
            problems.append(f"[P0] {relative(article)} 引用的图片不存在：{raw_ref}")
            continue
        if not is_within(target, figure_dir):
            problems.append(f"[P0] {relative(article)} 的本地正文图片必须位于本文章包 assets/figures/：{raw_ref}")
            continue
        used_figures.add(target)
        if target not in figure_paths:
            problems.append(f"[P0] {relative(article)} 引用的正文插图未登记到 article.json：{raw_ref}")

    for path in sorted(actual_figures - used_figures):
        warnings.append(f"[P1] {relative(path)} 未被正文引用。")
    for path in sorted(actual_archives & used_figures):
        problems.append(f"[P0] {relative(article)} 不得引用 assets/archive/ 中的历史文件。")
    for path in sorted(actual_covers & used_figures):
        problems.append(f"[P0] {relative(article)} 不得将封面作为正文图片引用。")

    return problems, warnings, cover_count, figure_count, archive_count


def main() -> int:
    parser = argparse.ArgumentParser(description="检查文章包图片资产。")
    parser.add_argument("--strict", action="store_true", help="将 P1 完整性提醒也作为失败。")
    args = parser.parse_args()

    if not ASSET_FILE.is_file():
        print(f"[P0] 缺少文章资产登记表：{relative(ASSET_FILE)}")
        return 1

    assets = parse_assets()
    problems: list[str] = []
    warnings: list[str] = []
    cover_count = figure_count = archive_count = 0
    for item in assets:
        item_problems, item_warnings, covers, figures, archives = check_article(item)
        problems.extend(item_problems)
        warnings.extend(item_warnings)
        cover_count += covers
        figure_count += figures
        archive_count += archives

    print("=== 文章包图片资产检查 ===")
    print(f"正式文章：{len(assets)} 篇；封面：{cover_count}；正文插图：{figure_count}；文章专属历史文件：{archive_count}")
    for message in problems + warnings:
        print(message)
    if problems:
        print(f"失败：P0={len(problems)}，P1={len(warnings)}")
        return 1
    if args.strict and warnings:
        print(f"失败：P0=0，P1={len(warnings)}（严格模式）")
        return 1
    print(f"通过：P0=0，P1={len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())