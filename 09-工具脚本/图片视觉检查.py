# -*- coding: utf-8 -*-
"""公众号正文图片视觉检查。

补足“图片存在但版式不适合发布”的漏检：
1. 检查正式文章实际引用的本地图片尺寸。
2. 用像素启发式检查重点内容是否贴边。
3. 生成 375px 手机宽度预览拼图，供终稿前人工快速复核段距、拥挤和裁切问题。

使用建议：
- 全仓巡检：python 09-工具脚本/图片视觉检查.py
- 新图终稿：python 09-工具脚本/图片视觉检查.py --focus 29 --strict

说明：像素检查只能发现明显风险，不能替代人工审美确认；最终发布前仍必须打开预览图检查。
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
MIN_WIDTH = 1200
MIN_HEIGHT = 675
SAFE_MARGIN_RATIO = 0.035
DARK_ROW_THRESHOLD = 24
DARK_COL_THRESHOLD = 24


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


def ink_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    rgb = img.convert("RGB")
    pix = rgb.load()
    w, h = rgb.size
    row_counts = [0] * h
    col_counts = [0] * w
    for y in range(h):
        for x in range(w):
            r, g, b = pix[x, y]
            # 只看较深的文字/图标，尽量排除浅色背景、网格和装饰色块。
            is_ink = r < 145 and g < 155 and b < 175
            if is_ink:
                row_counts[y] += 1
                col_counts[x] += 1
    rows = [i for i, c in enumerate(row_counts) if c >= DARK_ROW_THRESHOLD]
    cols = [i for i, c in enumerate(col_counts) if c >= DARK_COL_THRESHOLD]
    if not rows or not cols:
        return None
    return min(cols), min(rows), max(cols), max(rows)


def add_safety_issue(strict: bool, problems: list[str], warnings: list[str], message: str) -> None:
    if strict:
        problems.append(f"[P1] {message}")
    else:
        warnings.append(f"[P2] {message}")


def check_image(path: Path, strict: bool = False) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    try:
        with Image.open(path) as im:
            w, h = im.size
            rel = path.relative_to(ROOT)
            if w < MIN_WIDTH or h < MIN_HEIGHT:
                add_safety_issue(strict, problems, warnings, f"???????{rel} ({w}x{h})?????? {MIN_WIDTH}x{MIN_HEIGHT}")
            if w / h < 1.45 or w / h > 1.9:
                warnings.append(f"[P2] 图片比例不适合公众号横版信息图：{rel} ({w}x{h})")
            bbox = ink_bbox(im)
            if bbox:
                left, top, right, bottom = bbox
                safe = max(36, int(min(w, h) * SAFE_MARGIN_RATIO))
                if top < safe:
                    add_safety_issue(strict, problems, warnings, f"图片顶部安全区不足：{rel}，顶部重点像素约 {top}px，建议不少于 {safe}px")
                if left < safe:
                    add_safety_issue(strict, problems, warnings, f"图片左侧安全区不足：{rel}，左侧重点像素约 {left}px，建议不少于 {safe}px")
                if w - right < safe:
                    add_safety_issue(strict, problems, warnings, f"图片右侧安全区不足：{rel}，右侧留白约 {w-right}px，建议不少于 {safe}px")
                if h - bottom < safe:
                    add_safety_issue(strict, problems, warnings, f"图片底部安全区不足：{rel}，底部留白约 {h-bottom}px，建议不少于 {safe}px")
    except Exception as exc:
        problems.append(f"[P1] 图片无法打开：{path.relative_to(ROOT)}：{exc}")
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
    parser.add_argument("--strict", action="store_true", help="严格模式：安全区不足按 P1 阻断，适合新生成图片终稿检查")
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
    print(f"严格模式：{'开启' if args.strict else '关闭'}")
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
    print("说明：脚本只能发现明显安全区/尺寸风险；发布前仍需打开手机预览拼图人工确认段距、拥挤和裁切。")
    return 1 if p0 or p1 else 0


if __name__ == "__main__":
    sys.exit(main())
