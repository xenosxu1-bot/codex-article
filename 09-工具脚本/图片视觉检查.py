# -*- coding: utf-8 -*-
"""公众号正文图片视觉检查。

检查图片文件完整性并生成可选预览：
1. 检查正式文章实际引用的本地图片尺寸。
2. 不对比例、留白、位置或风格设置硬性要求。
3. 生成可选预览拼图，供人工判断是否适合目标平台。

使用建议：
- 全仓巡检：python 09-工具脚本/图片视觉检查.py
- 新图终稿：python 09-工具脚本/图片视觉检查.py --focus 29 --strict

说明：脚本不评价审美和模板符合度；预览仅供人工参考。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as exc:  # pragma: no cover
    print(f"[P1] 缺少图片检查依赖 Pillow：{exc}")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
ASSET_FILE = ROOT / "07-资料与流程" / "文章资产登记表.md"
PREVIEW_FILE = ROOT / ".tmp" / "图片视觉检查预览.jpg"
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_assets() -> list[Path]:
    files: list[Path] = []
    if not ASSET_FILE.exists():
        return files
    for line in ASSET_FILE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line or "编号" in line:
            continue
        cols = split_row(line)
        if len(cols) < 8 or not cols[0].isdigit():
            continue
        m = re.search(r"`([^`]+)`", cols[5])
        rel = m.group(1) if m else cols[5]
        article = ROOT / rel
        if article.exists():
            files.append(article)
    return files


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


def collect_images(article_files: list[Path]) -> list[Path]:
    images: list[Path] = []
    seen: set[Path] = set()
    for article in article_files:
        text = article.read_text(encoding="utf-8")
        for raw in IMAGE_RE.findall(text):
            target = resolve_markdown_path(article, raw)
            if target and target.exists() and target.suffix.lower() in IMAGE_EXTS and target not in seen:
                images.append(target)
                seen.add(target)
    return images


def font(size: int):
    for path in [Path(r"C:\Windows\Fonts\msyh.ttc"), Path(r"C:\Windows\Fonts\simhei.ttf"), Path(r"C:\Windows\Fonts\arial.ttf")]:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def check_image(path: Path, strict: bool = False) -> tuple[list[str], list[str]]:
    """只检查文件可读性；尺寸和版式仅作为非阻断提醒。"""
    problems: list[str] = []
    warnings: list[str] = []
    try:
        with Image.open(path) as im:
            w, h = im.size
            rel = path.relative_to(ROOT)
            if w <= 0 or h <= 0:
                problems.append(f"[P0] 图片尺寸无效：{rel} ({w}x{h})")
            elif w < 320 or h < 180:
                warnings.append(f"[P2] 图片像素较小，是否适合目标平台请人工判断：{rel} ({w}x{h})")
    except Exception as exc:
        problems.append(f"[P0] 图片无法打开：{path.relative_to(ROOT)}：{exc}")
    return problems, warnings

def make_preview(paths: list[Path]) -> None:
    if not paths:
        return
    thumb_w = 375
    label_h = 42
    gap = 18
    rows = []
    label_font = font(16)
    for idx, path in enumerate(paths, 1):
        with Image.open(path) as im:
            im = im.convert("RGB")
            ratio = thumb_w / im.width
            thumb_h = int(im.height * ratio)
            thumb = im.resize((thumb_w, thumb_h), Image.LANCZOS)
        row = Image.new("RGB", (thumb_w, thumb_h + label_h), "white")
        rd = ImageDraw.Draw(row)
        title = f"{idx:02d}  {path.name[:42]}"
        rd.text((8, 10), title, fill="#1F2937", font=label_font)
        row.paste(thumb, (0, label_h))
        rows.append(row)
    sheet_h = sum(r.height for r in rows) + gap * (len(rows) - 1)
    sheet = Image.new("RGB", (thumb_w, sheet_h), "#EEF4FF")
    y = 0
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height + gap
    PREVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW_FILE, quality=92)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查公众号正文图片视觉发布风险")
    parser.add_argument("--focus", help="只检查文件名或路径包含该关键词的图片，例如 29 或 Hermes")
    parser.add_argument("--strict", action="store_true", help="兼容旧命令；不再把尺寸、比例或安全区作为阻断条件")
    args = parser.parse_args()

    article_files = parse_assets()
    images = collect_images(article_files)
    if args.focus:
        images = [p for p in images if args.focus in p.name or args.focus in str(p.relative_to(ROOT))]

    problems: list[str] = []
    warnings: list[str] = []
    for path in images:
        ps, ws = check_image(path, strict=args.strict)
        problems.extend(ps)
        warnings.extend(ws)
    make_preview(images)
    print(f"正式文章引用图片：{len(images)} 张")
    if args.focus:
        print(f"检查范围：{args.focus}")
    print(f"严格模式参数：{'已传入但不改变视觉检查门槛' if args.strict else '未传入'}")
    print(f"手机预览拼图：{PREVIEW_FILE.relative_to(ROOT)}")
    if problems:
        print("\n阻断问题：")
        for item in problems:
            print(item)
    if warnings:
        print("\n提醒项：")
        for item in warnings[:30]:
            print(item)
        if len(warnings) > 30:
            print(f"……另有 {len(warnings)-30} 项提醒未显示")
    p0 = sum(1 for item in problems if item.startswith("[P0]"))
    p1 = sum(1 for item in problems if item.startswith("[P1]"))
    p2 = len(warnings)
    print(f"\n图片视觉检查：P0={p0} P1={p1} P2={p2}")
    print("说明：脚本只阻断图片损坏；尺寸、比例、留白和风格由人工按任务判断。")
    return 1 if p0 or p1 else 0


if __name__ == "__main__":
    sys.exit(main())
