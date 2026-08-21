#!/usr/bin/env python3
"""Render one article package as a local, mobile-friendly HTML preview."""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_RE = re.compile(r"(!\[[^\]]*\]\()([^\)]+)(\))")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render an article Markdown file to a local HTML preview")
    parser.add_argument("--article", required=True, help="article Markdown path relative to the repository")
    parser.add_argument("--output", required=True, help="HTML output path relative to the repository")
    return parser.parse_args()


def rewrite_image_urls(source: str, article_dir: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        alt, raw_path, closing = match.groups()
        path = raw_path.strip().strip("<>")
        if path.startswith(("http://", "https://", "data:")):
            return match.group(0)
        candidate = (article_dir / path).resolve()
        if candidate.is_file():
            return f"{alt}{candidate.as_uri()}{closing}"
        return match.group(0)

    return IMAGE_RE.sub(replace, source)


def render(article_path: Path, output_path: Path) -> None:
    source = article_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        rewrite_image_urls(source, article_path.parent),
        extensions=["fenced_code", "tables", "toc"],
        output_format="html5",
    )
    base_uri = article_path.parent.resolve().as_uri().rstrip("/") + "/"
    title_match = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else article_path.stem
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="{html.escape(base_uri, quote=True)}">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; color: #202124; background: #f5f6f8; }}
body {{ margin: 0; background: #f5f6f8; }}
main {{ width: min(760px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 64px; }}
article {{ background: #fff; border-radius: 16px; padding: 28px clamp(18px, 4vw, 42px); box-shadow: 0 8px 28px rgba(20, 30, 50, .08); overflow-wrap: anywhere; }}
h1 {{ font-size: clamp(28px, 6vw, 42px); line-height: 1.25; margin: 0 0 24px; }}
h2 {{ margin-top: 36px; padding-bottom: 8px; border-bottom: 1px solid #e7e9ee; font-size: clamp(22px, 4vw, 30px); }}
h3 {{ margin-top: 26px; font-size: 20px; }}
p, li {{ font-size: 17px; line-height: 1.9; }}
blockquote {{ margin: 20px 0; padding: 12px 16px; border-left: 4px solid #5878ff; background: #f3f6ff; color: #3d4658; }}
img {{ display: block; max-width: 100%; height: auto; margin: 22px auto; border-radius: 10px; }}
pre {{ overflow-x: auto; padding: 16px; border-radius: 10px; background: #1f2430; color: #eef2f7; line-height: 1.6; }}
code {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
:not(pre) > code {{ padding: 2px 5px; border-radius: 4px; background: #f0f2f5; }}
table {{ display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; }}
th, td {{ border: 1px solid #dfe3ea; padding: 8px 10px; white-space: nowrap; }}
a {{ color: #315efb; }}
@media (max-width: 480px) {{ main {{ width: calc(100% - 20px); padding-top: 10px; }} article {{ padding: 22px 16px; border-radius: 12px; }} p, li {{ font-size: 16px; line-height: 1.8; }} h1 {{ font-size: 28px; }} }}
</style>
</head>
<body><main><article>{body}</article></main></body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    article = Path(args.article)
    if not article.is_absolute():
        article = (REPO_ROOT / article).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = (REPO_ROOT / output).resolve()
    if not article.is_file():
        raise SystemExit(f"article not found: {article}")
    render(article, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
