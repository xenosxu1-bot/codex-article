#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查正式文章的资料核验记录，并由单篇元数据生成审查台账。

单篇 ``07-资料与流程/文章元数据/*.json`` 是机器可读的唯一事实来源；
``文章资料核验台账.md`` 仅是由本脚本生成的人工审查视图，禁止手工双写。
"""
from __future__ import annotations

import argparse
import datetime as date_time
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT / "07-资料与流程" / "文章元数据"
LEDGER_PATH = ROOT / "07-资料与流程" / "文章资料核验台账.md"
REQUIRED_ARTICLE_STATES = ("S5", "S6", "S7")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查文章资料核验元数据并生成审查台账")
    parser.add_argument(
        "--write-ledger",
        action="store_true",
        help="根据单篇元数据重建文章资料核验台账.md；省略时只检查其是否最新",
    )
    return parser.parse_args()


def text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def markdown_cell(value: str) -> str:
    return " ".join(value.replace("|", r"\|").splitlines()).strip()


def is_publishable_status(status: str) -> bool:
    return status.startswith(REQUIRED_ARTICLE_STATES)


def validate_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_records() -> tuple[list[dict[str, object]], list[str]]:
    records: list[dict[str, object]] = []
    issues: list[str] = []
    today = date_time.date.today()
    files = sorted(METADATA_DIR.glob("*.json"), key=lambda path: path.name)
    if not files:
        return records, [f"[P0] 未找到文章元数据目录或 JSON：{METADATA_DIR.relative_to(ROOT)}"]

    for path in files:
        label = path.relative_to(ROOT).as_posix()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            issues.append(f"[P0] 无法读取元数据 {label}：{error}")
            continue
        if not isinstance(raw, dict):
            issues.append(f"[P0] 元数据根节点必须是对象：{label}")
            continue

        article = raw.get("article")
        if not isinstance(article, dict):
            issues.append(f"[P0] 元数据缺少 article 对象：{label}")
            continue
        article_id = text(article.get("id"))
        title = text(article.get("title"))
        article_path = text(article.get("path"))
        status = text(article.get("status"))
        if not article_id.isdigit() or not title or not article_path:
            issues.append(f"[P0] 元数据 article.id、article.title、article.path 必须完整：{label}")
            continue

        sources = raw.get("sources")
        if not isinstance(sources, list):
            issues.append(f"[P0] 元数据 sources 必须是列表：{label}")
            continue
        if is_publishable_status(status) and not sources:
            issues.append(f"[P0] 准备入库或发布的文章缺少资料来源：{label}")

        valid_sources: list[dict[str, str]] = []
        for index, source in enumerate(sources, start=1):
            source_label = f"{label}:sources[{index}]"
            if not isinstance(source, dict):
                issues.append(f"[P0] 资料来源必须是对象：{source_label}")
                continue
            source_title = text(source.get("title"))
            url = text(source.get("url"))
            checked_at = text(source.get("checked_at"))
            notes = text(source.get("notes"))
            if not source_title or not validate_url(url) or not checked_at or not notes:
                issues.append(f"[P0] 资料来源必须包含 title、http(s) url、checked_at、notes：{source_label}")
                continue
            try:
                checked_date = date_time.date.fromisoformat(checked_at)
            except ValueError:
                issues.append(f"[P0] 核验日期必须是 YYYY-MM-DD：{source_label}")
                continue
            if checked_date > today:
                issues.append(f"[P0] 核验日期不能晚于今天：{source_label}")
                continue
            valid_sources.append({
                "title": source_title,
                "url": url,
                "checked_at": checked_at,
                "notes": notes,
            })

        records.append({
            "id": article_id.zfill(2),
            "title": title,
            "path": article_path.replace("\\", "/"),
            "status": status,
            "sources": valid_sources,
        })

    records.sort(key=lambda item: (int(str(item["id"])), str(item["title"])))
    return records, issues


def render_ledger(records: list[dict[str, object]]) -> str:
    lines = [
        "# 文章资料核验台账",
        "",
        "> **生成文件**：由 `python 09-工具脚本/资料核验检查.py --write-ledger` 根据单篇元数据 JSON 自动重建；不要手工编辑来源条目。",
        "> **唯一事实来源**：`07-资料与流程/文章元数据/*.json`。本台账用于人工审查、复核与定位，不构成第二份可编辑主数据。",
        "> 涉及产品能力、版本、价格、权限、标准、政策或安全结论时，发布前仍须重新核对快速变化的信息。",
        "",
        "| 编号 | 文章 | 核验日期 | 来源 | 链接 | 核验用途与边界 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        article_path = "../" + str(record["path"]).lstrip("/")
        article_link = f"[{markdown_cell(str(record['title']))}](<{article_path}>)"
        for source in record["sources"]:
            assert isinstance(source, dict)
            url = markdown_cell(str(source["url"]))
            lines.append(
                "| {id} | {article} | {date} | {title} | [{url}]({url}) | {notes} |".format(
                    id=record["id"],
                    article=article_link,
                    date=markdown_cell(str(source["checked_at"])),
                    title=markdown_cell(str(source["title"])),
                    url=url,
                    notes=markdown_cell(str(source["notes"])),
                )
            )
    lines.extend([
        "",
        "## 使用说明",
        "",
        "1. 新文章正文默认不添加来源链接章节，避免把维护型资料入口混入读者阅读流。",
        "2. 新文章完成资料核验后，只编辑单篇元数据 JSON 的 `sources`；运行本脚本重建本台账。",
        "3. 发布记录只记录“资料已核验”及对应文章编号，不重复粘贴整组 URL。",
        "4. 一键发布检查会校验元数据字段，并确保本台账与元数据完全一致。",
        "",
    ])
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def main() -> int:
    args = parse_args()
    records, issues = load_records()
    if issues:
        print("\n".join(issues))
        return 1

    expected = render_ledger(records)
    current = LEDGER_PATH.read_text(encoding="utf-8") if LEDGER_PATH.exists() else None
    if args.write_ledger:
        if current != expected:
            write_text(LEDGER_PATH, expected)
            print(f"已重建资料核验台账：{LEDGER_PATH.relative_to(ROOT)}")
        else:
            print("资料核验台账已是最新版本。")
    elif current != expected:
        print(f"[P0] 资料核验台账缺失或已过期：{LEDGER_PATH.relative_to(ROOT)}")
        print("请运行：python 09-工具脚本/资料核验检查.py --write-ledger")
        return 1

    source_count = sum(len(record["sources"]) for record in records)
    print({"metadataFiles": len(records), "sourceRecords": source_count, "ledger": str(LEDGER_PATH.relative_to(ROOT))})
    print("资料核验检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())