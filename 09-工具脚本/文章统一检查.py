#!/usr/bin/env python3
"""按文章编号调用 article-Skill 的统一检查器。"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "09-工具脚本" / "article-skill-project.json"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按文章编号执行统一文章检查")
    parser.add_argument("--id", help="两位或更多位文章编号，例如 29")
    parser.add_argument("--article", help="正文相对路径；不传则按编号定位")
    parser.add_argument("--manifest", help="元数据相对路径；不传则按编号定位")
    parser.add_argument("--tier", choices=("quick", "standard", "deep"), help="生产层级；不传则读取元数据")
    parser.add_argument("--skill-root", help="article-wechat Skill 根目录")
    parser.add_argument("--strict", action="store_true", help="将 P1 建议视为未通过")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    return parser.parse_args()

def normalize_id(value: str) -> str:
    if not value or not value.isdigit():
        raise ValueError("--id 必须为数字")
    return f"{int(value):02d}"

def locate_one(pattern: str, label: str) -> Path:
    matches = sorted(REPO_ROOT.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"{label}应为 1 个，当前为 {len(matches)}：{pattern}")
    return matches[0]

def locate_skill_root(arg_value: str | None) -> Path:
    candidates = [arg_value, os.getenv("ARTICLE_SKILL_ROOT"), str(Path.home() / ".codex" / "skills" / "article-wechat")]
    for value in candidates:
        if not value:
            continue
        root = Path(value).expanduser().resolve()
        if (root / "scripts" / "validate_article_package.py").is_file():
            return root
    raise FileNotFoundError("未找到 article-wechat Skill。请传入 --skill-root，或设置 ARTICLE_SKILL_ROOT。")

def main() -> int:
    args = parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not args.id and not args.article:
        raise ValueError("请提供 --id 或 --article")
    article = Path(args.article) if args.article else locate_one(f"[0-9][0-9]-*/{normalize_id(args.id)}-*.md", "编号对应正文")
    if not article.is_absolute():
        article = (REPO_ROOT / article).resolve()
    manifest = Path(args.manifest) if args.manifest else locate_one(f"07-资料与流程/文章元数据/{normalize_id(args.id)}-*.json", "编号对应元数据")
    if not manifest.is_absolute():
        manifest = (REPO_ROOT / manifest).resolve()
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    tier = args.tier or manifest_data.get("article", {}).get("tier", "standard")
    skill_root = locate_skill_root(args.skill_root)
    checker = skill_root / "scripts" / "validate_article_package.py"
    command = [sys.executable, str(checker), "--root", str(REPO_ROOT), "--config", str(CONFIG_PATH), "--article", str(article.relative_to(REPO_ROOT)), "--manifest", str(manifest.relative_to(REPO_ROOT)), "--tier", tier]
    if args.strict:
        command.append("--strict")
    if args.json:
        command.append("--json")
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"统一检查未执行：{error}", file=sys.stderr)
        raise SystemExit(2)
