# -*- coding: utf-8 -*-
"""
批量补全微信公众号文章封面图。

用途：
- 按文章文件名生成同名封面：编号-标题-封面.png
- 固定输出 1792×764，比例约 2.35:1
- 风格遵循 article-wechat 封面规范：深色 AI 科技风、左侧标题与副标题、右侧产品工作台、底部能力标签
- 默认只补缺失或尺寸不合规的封面；如需全部重绘，可加 --force
"""
from __future__ import annotations

from pathlib import Path
import argparse
import math
import random
import re
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1792, 764
COVER_DIR = ROOT / "08-素材库" / "图片" / "文章封面"
PREVIEW_NAME = "00-封面补全预览-01-26.png"
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

PALETTES = {
    "Codex": ((40, 178, 255), (142, 93, 255), (7, 18, 38)),
    "AI": ((40, 226, 160), (45, 154, 255), (4, 22, 36)),
    "安全": ((66, 224, 168), (110, 135, 255), (4, 28, 40)),
    "内容": ((255, 155, 85), (176, 96, 255), (25, 13, 40)),
    "PPT": ((255, 178, 70), (70, 170, 255), (28, 20, 36)),
    "默认": ((46, 185, 255), (148, 94, 255), (5, 16, 36)),
}

KEYWORD_BANK = [
    ("需求拆解", "目标清晰"),
    ("资料核验", "可信来源"),
    ("工作流", "自动执行"),
    ("结果交付", "可复用"),
]

ARTICLE_SPEC = {
    1: ("Codex 新手上手", "从界面到第一个高质量任务", ["任务入口", "权限确认", "文件协作", "结果验收"]),
    2: ("Codex 进阶提效", "配置、权限、复用与自动化", ["配置优化", "权限可控", "模板复用", "自动化"]),
    3: ("Codex 实战修复", "从失败测试到可验证交付", ["问题定位", "补丁生成", "测试验证", "交付记录"]),
    4: ("AGENTS.md 模板", "让 Codex 按团队规则工作", ["规则沉淀", "协作约束", "验收标准", "团队一致"]),
    5: ("Codex 插件与 Skill", "把常用能力装进工作流", ["插件扩展", "Skill 沉淀", "工作流集成", "团队共享"]),
    6: ("AI 学习小程序", "跟着 weStudy 做实战", ["需求设计", "页面搭建", "AI 能力", "上线验证"]),
    7: ("入口 Agent 化", "别只盯 GPT-5.6", ["任务入口", "工具调用", "上下文", "交付闭环"]),
    8: ("可交付工作流", "别再只会问 AI", ["需求拆解", "调研产出", "校验归档", "持续复用"]),
    9: ("Codex 与 Skills", "智能体工作流中文参考", ["指令规范", "技能复用", "工具协同", "质量检查"]),
    10: ("AI 深度调研", "从资料到可核查报告", ["限定来源", "证据链", "交叉核验", "报告交付"]),
    11: ("AI 编程 Agent", "从想法到可验证交付", ["需求文档", "原型实现", "测试部署", "人工验收"]),
    12: ("一人 AI 工作台", "1 主模型 + 3 专项工具", ["主模型", "深度研究", "自动化", "图像视频"]),
    13: ("AI 内容工作流", "选题、资料、核查、改写", ["选题判断", "资料整理", "事实核查", "人味改写"]),
    14: ("AI Agent 边界", "从会提问到会委托", ["资料收集", "方案生成", "网页搭建", "流程自动化"]),
    15: ("验收标准", "AI 越快越要会验收", ["需求表达", "质量标准", "事实检查", "版本留痕"]),
    16: ("一人 AI 轻量团队", "内容、调研、客服、自动化", ["内容助理", "调研助理", "客服助理", "流程助理"]),
    17: ("数据权限边界", "AI 工具越强越要安全", ["敏感数据", "权限控制", "输出审校", "留痕追责"]),
    18: ("MCP 工具连接", "从接口到 Agent 化搜索", ["工具协议", "上下文", "任务调用", "可观测"]),
    19: ("业务上下文", "AI 不懂业务的真正原因", ["流程资料", "决策规则", "案例沉淀", "持续更新"]),
    20: ("30 天 AI 能力地图", "不从 100 个 Prompt 开始", ["提问能力", "拆解能力", "工作流", "项目实战"]),
    21: ("AI 做 PPT", "排版之前先防失真", ["结构先行", "资料核验", "图表一致", "演示验收"]),
    22: ("AI 操作电脑", "先设权限再谈自动化", ["权限分级", "人工确认", "失败回滚", "验收清单"]),
    23: ("Data Agent 落地", "企业 AI ROI 从流程开始", ["数据流程", "指标定义", "异常修复", "业务闭环"]),
    24: ("多 Agent 生产系统", "可验证协作不是群聊", ["角色分工", "状态可见", "交付契约", "质量闸口"]),
    25: ("AI 论文趋势", "从模型能力到系统能力", ["研究方向", "工程系统", "评测基准", "落地场景"]),
    26: ("OpenClaw 上手", "把 AI 助手接进聊天软件", ["聊天入口", "智能回复", "流程连接", "日常协作"]),
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int, max_lines: int) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(text):
        match = re.match(r"[A-Za-z0-9.+/#-]+", text[i:])
        if match:
            tokens.append(match.group(0))
            i += len(match.group(0))
        else:
            tokens.append(text[i])
            i += 1
    lines, current = [], ""
    for token in tokens:
        candidate = current + token
        if not current or text_size(draw, candidate, fnt)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = token
            if len(lines) == max_lines - 1:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines]


def article_number(article_path: Path) -> int:
    match = re.match(r"^(\d+)-", article_path.stem)
    return int(match.group(1)) if match else 999


def scan_articles() -> list[Path]:
    articles: list[Path] = []
    for directory in sorted(ROOT.iterdir()):
        if not directory.is_dir() or not re.match(r"^0[1-6]-", directory.name):
            continue
        for article in directory.glob("*.md"):
            if article.name.lower() != "readme.md":
                articles.append(article)
    return sorted(articles, key=article_number)


def split_title(article: Path) -> tuple[str, str, list[str]]:
    number = article_number(article)
    if number in ARTICLE_SPEC:
        return ARTICLE_SPEC[number]
    title = re.sub(r"^\d+-", "", article.stem)
    parts = re.split(r"[:：]", title, maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1], [k[0] for k in KEYWORD_BANK]
    return title[:14], title[14:] or "AI 技术实战指南", [k[0] for k in KEYWORD_BANK]


def choose_palette(title: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    if "安全" in title or "权限" in title or "边界" in title:
        return PALETTES["安全"]
    if "内容" in title or "PPT" in title:
        return PALETTES["内容"] if "PPT" not in title else PALETTES["PPT"]
    if "Codex" in title or "OpenClaw" in title:
        return PALETTES["Codex"]
    if "AI" in title or "Agent" in title:
        return PALETTES["AI"]
    return PALETTES["默认"]


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color: tuple[int, int, int], kind: int) -> None:
    cx, cy = x + size // 2, y + size // 2
    w = max(3, size // 12)
    if kind % 5 == 0:
        draw.rounded_rectangle((x+12, y+16, x+size-12, y+size-16), radius=9, outline=color, width=w)
        draw.line((cx, y+8, cx, y+16), fill=color, width=w)
        draw.line((cx, y+size-16, cx, y+size-8), fill=color, width=w)
    elif kind % 5 == 1:
        draw.polygon([(cx, y+8), (x+size-10, cy), (cx, y+size-8), (x+10, cy)], outline=color, fill=None)
        draw.ellipse((cx-7, cy-7, cx+7, cy+7), fill=color)
    elif kind % 5 == 2:
        for n in range(3):
            draw.rounded_rectangle((x+10+n*24, y+12+n*12, x+34+n*24, y+36+n*12), radius=5, outline=color, width=w)
        draw.line((x+34, y+24, x+58, y+36, x+82, y+48), fill=color, width=w)
    elif kind % 5 == 3:
        draw.line((x+14, y+size-18, x+size-14, y+18), fill=color, width=w)
        draw.line((x+size-34, y+18, x+size-14, y+18, x+size-14, y+38), fill=color, width=w)
        for n in range(4):
            draw.rounded_rectangle((x+16+n*20, y+size-20-n*12, x+30+n*20, y+size-8), radius=3, fill=color)
    else:
        draw.polygon([(x+size*0.50, y+8), (x+size*0.62, y+size*0.42), (x+size-10, y+size*0.42), (x+size*0.56, y+size-8), (x+size*0.66, y+size*0.56), (x+12, y+size*0.56)], fill=color)


def glow_layer() -> Image.Image:
    return Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))


def create_cover(article: Path, output: Path) -> None:
    main_title, subtitle, keywords = split_title(article)
    accent1, accent2, bg_base = choose_palette(main_title + subtitle)
    random.seed(article_number(article) * 97)

    img = Image.new("RGB", (WIDTH, HEIGHT), bg_base)
    pix = img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            gx = x / WIDTH
            gy = y / HEIGHT
            r = int(bg_base[0] + 13 * gx + 4 * gy)
            g = int(bg_base[1] + 20 * gx + 5 * gy)
            b = int(bg_base[2] + 56 * gx + 8 * gy)
            pix[x, y] = (min(255, r), min(255, g), min(255, b))

    draw = ImageDraw.Draw(img, "RGBA")

    # 右侧环境光与底部光带
    for radius, alpha in [(420, 34), (290, 46), (170, 60)]:
        box = (WIDTH-560-radius, 44-radius//2, WIDTH-560+radius, 44+radius)
        draw.ellipse(box, fill=(*accent1, alpha))
    for i in range(16):
        y = 640 + i * 7
        draw.arc((760-i*28, y-120, 1820+i*18, y+260), 185, 356, fill=(*accent1, max(16, 72-i*4)), width=2)

    # 微弱粒子与网格
    for _ in range(130):
        x = random.randint(0, WIDTH-1); y = random.randint(0, HEIGHT-1)
        a = random.randint(20, 70)
        draw.ellipse((x, y, x+2, y+2), fill=(*accent1, a))
    for x in range(860, WIDTH, 58):
        draw.line((x, 90, x-280, HEIGHT-70), fill=(70, 160, 255, 22), width=1)
    for y in range(120, HEIGHT, 52):
        draw.line((820, y, WIDTH-80, y+20), fill=(120, 80, 255, 18), width=1)

    # 左侧标题区，保持 55%-60% 干净空间
    left_x, top_y = 62, 72
    badge_text = f"第 {article_number(article):02d} 篇 · AI 实战指南"
    rounded(draw, (left_x, top_y-22, left_x+360, top_y+38), 30, (*accent1, 215))
    draw.text((left_x+34, top_y-10), badge_text, font=font(28, True), fill=(2, 18, 32, 255))

    title_font = font(78, True) if len(main_title) <= 11 else font(68, True)
    y = top_y + 94
    for idx, line in enumerate(wrap_text(draw, main_title, title_font, 760, 2)):
        # 白色主体 + 局部强调色阴影，增强公众号头图冲击力
        draw.text((left_x+3, y+4), line, font=title_font, fill=(0, 0, 0, 120))
        fill = (246, 252, 255, 255) if idx == 0 else (*accent1, 255)
        draw.text((left_x, y), line, font=title_font, fill=fill)
        y += text_size(draw, line, title_font)[1] + 24

    sub_font = font(40, True)
    y += 12
    draw.text((left_x, y), subtitle, font=sub_font, fill=(235, 244, 255, 255))
    y += 58
    draw.line((left_x, y, left_x+705, y), fill=(*accent2, 160), width=2)

    # 右侧主题视觉：产品工作台 + 代码卡片 + 自动化节点，无人物元素
    panel_x, panel_y, panel_w, panel_h = 835, 64, 690, 510
    shadow = glow_layer(); sd = ImageDraw.Draw(shadow, "RGBA")
    rounded(sd, (panel_x-8, panel_y-8, panel_x+panel_w+8, panel_y+panel_h+8), 32, (*accent1, 28))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18)); img.alpha_composite(shadow) if img.mode == 'RGBA' else None
    draw = ImageDraw.Draw(img, "RGBA")
    rounded(draw, (panel_x, panel_y, panel_x+panel_w, panel_y+panel_h), 28, (6, 14, 32, 222), (*accent1, 180), 2)
    draw.text((panel_x+36, panel_y+30), "AI Workspace", font=font(30, True), fill=(238, 248, 255, 255))
    for i, label in enumerate(["Plan", "Research", "Build", "Review"]):
        bx = panel_x+38+i*152
        rounded(draw, (bx, panel_y+92, bx+124, panel_y+170), 14, (18, 42, 78, 190), (70, 160, 255, 100), 1)
        draw_icon(draw, bx+14, panel_y+106, 46, accent1 if i % 2 == 0 else accent2, i)
        draw.text((bx+66, panel_y+108), label, font=font(22, True), fill=(236, 244, 255, 255))
    # 中部任务列表
    for i in range(4):
        yy = panel_y+210+i*58
        rounded(draw, (panel_x+38, yy, panel_x+panel_w-42, yy+42), 12, (15, 31, 60, 178), (76, 140, 255, 55), 1)
        draw.rounded_rectangle((panel_x+58, yy+11, panel_x+85, yy+34), radius=5, fill=(*accent1, 210))
        draw.text((panel_x+104, yy+7), ["需求拆解", "资料核验", "工具调用", "交付归档"][i], font=font(22, True), fill=(230, 240, 255, 255))
        draw.text((panel_x+panel_w-175, yy+8), ["Ready", "Verified", "Running", "Done"][i], font=font(20), fill=(*accent2, 240))
    # 底部流程
    flow_y = panel_y + 462
    for i, label in enumerate(["输入", "理解", "执行", "交付"]):
        bx = panel_x+62+i*148
        rounded(draw, (bx, flow_y, bx+92, flow_y+46), 12, (20, 45, 88, 210), (*accent1, 105), 1)
        draw.text((bx+23, flow_y+9), label, font=font(20, True), fill=(234, 248, 255, 255))
        if i < 3:
            draw.line((bx+96, flow_y+23, bx+132, flow_y+23), fill=(*accent1, 180), width=3)
            draw.polygon([(bx+132, flow_y+23), (bx+122, flow_y+16), (bx+122, flow_y+30)], fill=(*accent1, 180))

    # 右侧两张代码/Agent 卡片
    for i, (cx, cy, title) in enumerate([(1550, 110, "Agent"), (1548, 330, "Skill")]):
        rounded(draw, (cx, cy, WIDTH-42, cy+164), 20, (9, 20, 48, 205), (*accent2, 155), 2)
        draw.text((cx+28, cy+22), title, font=font(26, True), fill=(236, 246, 255, 255))
        for j in range(4):
            draw.text((cx+30, cy+62+j*22), f"{j+1}  // {['call tool','check data','run flow','return'][j]}", font=font(18), fill=((accent1 if j%2 else (140,170,210)) + (210,)))

    # 中央小型 3D 芯片/立方体
    cx, cy = 1230, 598
    draw.ellipse((cx-152, cy-38, cx+152, cy+52), fill=(*accent1, 32), outline=(*accent1, 125), width=2)
    rounded(draw, (cx-72, cy-128, cx+72, cy+18), 28, (32, 70, 150, 220), (*accent2, 220), 3)
    draw.text((cx-42, cy-94), "AI", font=font(58, True), fill=(230, 247, 255, 255))
    draw.line((cx-72, cy-6, cx+72, cy-6), fill=(*accent1, 160), width=2)

    # 底部四个能力标签，图标与文字居中
    card_y, card_h = 612, 106
    card_x, card_w = 62, 820
    rounded(draw, (card_x, card_y, card_x+card_w, card_y+card_h), 20, (5, 18, 42, 210), (*accent1, 140), 2)
    slots = 4
    for i in range(slots):
        sx = card_x + i * (card_w // slots)
        if i > 0:
            draw.line((sx, card_y+20, sx, card_y+card_h-20), fill=(*accent1, 88), width=1)
        icon_size = 48
        icon_x = sx + 22
        icon_y = card_y + 29
        draw_icon(draw, icon_x, icon_y, icon_size, accent1 if i % 2 == 0 else accent2, i+1)
        label = keywords[i] if i < len(keywords) else KEYWORD_BANK[i][0]
        desc = KEYWORD_BANK[i][1]
        text_x = icon_x + 66
        draw.text((text_x, card_y+24), label, font=font(25, True), fill=(242, 250, 255, 255))
        draw.text((text_x, card_y+61), desc, font=font(18), fill=(180, 205, 230, 235))

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "PNG", optimize=True)


def make_preview(covers: Iterable[Path]) -> None:
    cover_list = list(covers)
    if not cover_list:
        return
    thumb_w, thumb_h = 448, 191
    cols = 4
    rows = math.ceil(len(cover_list) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 34)), (7, 12, 24))
    draw = ImageDraw.Draw(sheet)
    caption_font = font(18)
    for idx, cover in enumerate(cover_list):
        with Image.open(cover) as im:
            thumb = im.resize((thumb_w, thumb_h), Image.LANCZOS).convert("RGB")
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + 34)
        sheet.paste(thumb, (x, y))
        name = cover.stem.replace("-封面", "")
        draw.text((x + 8, y + thumb_h + 7), name[:34], font=caption_font, fill=(210, 225, 245))
    sheet.save(COVER_DIR / PREVIEW_NAME, "PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="批量补全微信公众号文章封面图")
    parser.add_argument("--force", action="store_true", help="重新生成所有封面")
    parser.add_argument("--only", type=int, nargs="*", help="只处理指定编号，例如 --only 26")
    args = parser.parse_args()

    articles = scan_articles()
    generated: list[Path] = []
    all_covers: list[Path] = []
    for article in articles:
        number = article_number(article)
        if args.only and number not in args.only:
            continue
        output = COVER_DIR / f"{article.stem}-封面.png"
        needs_update = args.force or not output.exists()
        if output.exists() and not args.force:
            try:
                with Image.open(output) as im:
                    needs_update = im.size != (WIDTH, HEIGHT)
            except Exception:
                needs_update = True
        if needs_update:
            create_cover(article, output)
            generated.append(output)
        all_covers.append(output)

    # 预览图始终按全部正式封面生成，方便人工检查整体风格。
    official = [COVER_DIR / f"{article.stem}-封面.png" for article in articles]
    make_preview(official)

    print(f"文章数量：{len(articles)}")
    print(f"本次生成：{len(generated)}")
    for item in generated:
        print(item.name)
    print(f"预览图：{COVER_DIR / PREVIEW_NAME}")


if __name__ == "__main__":
    main()
