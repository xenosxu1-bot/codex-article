from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

repo = Path(__file__).resolve().parent
imgdir = repo / "images"
font_path = r"C:\Windows\Fonts\msyh.ttc"
font_bold_path = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size):
    return ImageFont.truetype(font_path, size)


def bold(size):
    return ImageFont.truetype(font_bold_path, size)


TITLE = bold(54)
SUB = font(30)
CARD = bold(30)
SMALL = font(24)

COL = {
    "navy": (10, 18, 38),
    "blue": (37, 99, 235),
    "cyan": (6, 182, 212),
    "green": (16, 185, 129),
    "orange": (249, 115, 22),
    "pink": (236, 72, 153),
    "purple": (124, 58, 237),
    "yellow": (250, 204, 21),
    "white": (255, 255, 255),
}


def fit_cover(im, size):
    w, h = size
    target = w / h
    current = im.width / im.height
    if current > target:
        new_w = int(im.height * target)
        x = (im.width - new_w) // 2
        im = im.crop((x, 0, x + new_w, im.height))
    else:
        new_h = int(im.width / target)
        y = (im.height - new_h) // 2
        im = im.crop((0, y, im.width, y + new_h))
    return im.resize(size, Image.Resampling.LANCZOS)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def write(draw, xy, s, f, fill=COL["white"]):
    draw.text(xy, s, font=f, fill=fill)


def shadow_text(draw, xy, s, f, fill=COL["white"]):
    x, y = xy
    draw.text((x + 3, y + 3), s, font=f, fill=(0, 0, 0, 120))
    draw.text((x, y), s, font=f, fill=fill)


def bg_from(name, size=(1280, 720), blur=7):
    im = fit_cover(Image.open(imgdir / name).convert("RGB"), size).filter(ImageFilter.GaussianBlur(blur))
    overlay = Image.new("RGBA", size, (7, 14, 32, 172))
    im = im.convert("RGBA")
    im.alpha_composite(overlay)
    return im.convert("RGB")


def chip(draw, x, y, label, color):
    w = int(draw.textlength(label, font=SMALL)) + 36
    rounded(draw, [x, y, x + w, y + 50], 25, color)
    write(draw, (x + 18, y + 10), label, SMALL)
    return x + w + 16


def card(draw, x, y, w, h, title, body, color):
    rounded(draw, [x, y, x + w, y + h], 22, (255, 255, 255), outline=(220, 230, 245), width=2)
    rounded(draw, [x, y, x + 12, y + h], 8, color)
    write(draw, (x + 32, y + 20), title, CARD, (15, 23, 42))
    yy = y + 70
    for line in body.split("\n"):
        write(draw, (x + 32, yy), line, SMALL, (71, 85, 105))
        yy += 34


def hero(out, src, title, subtitle, chips, accent=COL["cyan"]):
    canvas = bg_from(src)
    draw = ImageDraw.Draw(canvas)
    rounded(draw, [42, 38, 720, 188], 24, (8, 13, 30), outline=(51, 65, 85), width=2)
    shadow_text(draw, (62, 62), title, TITLE)
    shadow_text(draw, (64, 132), subtitle, SUB, (241, 245, 249))
    x = 64
    for label, color in chips:
        x = chip(draw, x, 610, label, color)
    shot = fit_cover(Image.open(imgdir / src).convert("RGB"), (520, 340))
    rounded(draw, [694, 210, 1226, 562], 28, (255, 255, 255), outline=accent, width=5)
    canvas.paste(shot, (700, 216))
    draw.rounded_rectangle([700, 216, 1220, 556], radius=22, outline=(255, 255, 255), width=2)
    canvas.save(imgdir / out, quality=94)


def flow_debug():
    canvas = Image.new("RGB", (1280, 720), (248, 250, 252))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 1280, 110], fill=COL["navy"])
    write(draw, (54, 30), "Codex Debug 闭环：从失败测试到可验证修复", TITLE)
    steps = [
        ("1 复现问题", "错误日志\n失败测试\n操作步骤", COL["blue"]),
        ("2 定位根因", "先解释原因\n再动手修改", COL["purple"]),
        ("3 最小修复", "不改公开 API\n不扩大范围", COL["orange"]),
        ("4 跑测试", "最小相关测试\n失败继续追", COL["green"]),
        ("5 Review", "审查 diff\n人工确认", COL["pink"]),
    ]
    x = 50
    for i, (title, body, color) in enumerate(steps):
        card(draw, x, 170, 220, 250, title, body, color)
        x += 245
        if i < 4:
            draw.line([x - 20, 295, x + 10, 295], fill=(100, 116, 139), width=5)
            draw.polygon([(x + 10, 295), (x - 6, 285), (x - 6, 305)], fill=(100, 116, 139))
    write(draw, (70, 610), "推荐提示词：先复现/定位，再修复/验证，最后报告命令和结果", SUB, (15, 23, 42))
    canvas.save(imgdir / "07-debug-loop-cn.jpg", quality=94)


def agents_template():
    canvas = Image.new("RGB", (1280, 720), COL["navy"])
    draw = ImageDraw.Draw(canvas)
    write(draw, (54, 42), "AGENTS.md：把团队规则写进 Codex 默认上下文", TITLE)
    write(draw, (58, 112), "一次写好，后续每个任务都少解释一遍", SUB, (226, 232, 240))
    blocks = [
        ("项目命令", "安装 / 构建 / 测试 / lint", COL["blue"]),
        ("代码约定", "依赖、API、命名、架构边界", COL["green"]),
        ("完成标准", "跑哪些检查，如何汇报结果", COL["orange"]),
        ("Review 指南", "正确性、安全、回归、测试", COL["purple"]),
    ]
    x, y = 70, 210
    for title, body, color in blocks:
        card(draw, x, y, 535, 160, title, body, color)
        if x == 70:
            x = 675
        else:
            x = 70
            y += 190
    rounded(draw, [70, 610, 1210, 675], 22, (30, 41, 59), outline=(71, 85, 105), width=2)
    write(draw, (95, 626), "口诀：重复提醒两次的规则，就应该沉淀进 AGENTS.md", SUB, COL["yellow"])
    canvas.save(imgdir / "08-agents-template-cn.jpg", quality=94)


def safety():
    canvas = Image.new("RGB", (1280, 720), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 1280, 110], fill=(127, 29, 29))
    write(draw, (54, 30), "Codex 安全边界：权限越大，越要可审查", TITLE)
    zones = [
        ("read-only", "只读调研\n理解项目 / 审查代码", COL["green"]),
        ("workspace-write", "日常开发默认\n工作区内读写", COL["blue"]),
        ("danger-full-access", "谨慎使用\n仅限隔离可信环境", COL["orange"]),
    ]
    x = 70
    for title, body, color in zones:
        rounded(draw, [x, 175, x + 350, 430], 26, (248, 250, 252), outline=color, width=5)
        write(draw, (x + 30, 205), title, CARD, (15, 23, 42))
        yy = 270
        for line in body.split("\n"):
            write(draw, (x + 30, yy), line, SMALL, (51, 65, 85))
            yy += 42
        x += 410
    warnings = ["不要提交 API key", "联网权限按需打开", "提交前看 diff", "让 Codex 跑最小验证"]
    x, y = 80, 545
    for label in warnings:
        x = chip(draw, x, y, label, COL["pink"])
    canvas.save(imgdir / "09-safety-cn.jpg", quality=94)


def cheat():
    canvas = Image.new("RGB", (1280, 720), (15, 23, 42))
    draw = ImageDraw.Draw(canvas)
    write(draw, (54, 36), "Codex 速查表：常用命令 + 高质量提示词", TITLE)
    left = [
        ("/plan", "先规划，不改文件"),
        ("/review", "审查当前 diff"),
        ("/model", "切换模型和推理强度"),
        ("/status", "查看权限、模型、上下文"),
        ("/diff", "查看 Git 改动"),
    ]
    right = [("Goal", "要做什么"), ("Context", "相关文件/日志/截图"), ("Constraints", "不能改什么"), ("Done when", "如何验证完成")]
    rounded(draw, [60, 140, 600, 640], 28, (255, 255, 255))
    write(draw, (95, 170), "Slash Commands", CARD, (15, 23, 42))
    y = 230
    for cmd, desc in left:
        write(draw, (95, y), cmd, CARD, COL["blue"])
        write(draw, (230, y + 3), desc, SMALL, (51, 65, 85))
        y += 72
    rounded(draw, [680, 140, 1220, 640], 28, (255, 255, 255))
    write(draw, (715, 170), "Prompt 四要素", CARD, (15, 23, 42))
    y = 235
    for key, value in right:
        rounded(draw, [715, y, 875, y + 48], 20, COL["orange"])
        write(draw, (736, y + 8), key, SMALL)
        write(draw, (905, y + 8), value, SMALL, (51, 65, 85))
        y += 82
    canvas.save(imgdir / "10-cheatsheet-cn.jpg", quality=94)


def plugin_skill_cover():
    canvas = bg_from("01-codex-app-cn.jpg")
    draw = ImageDraw.Draw(canvas)
    rounded(draw, [42, 38, 760, 198], 24, (8, 13, 30), outline=(51, 65, 85), width=2)
    shadow_text(draw, (62, 62), "Codex 插件与 Skills", TITLE)
    shadow_text(draw, (64, 134), "把浏览器、设计、文档、内容创作能力装进工作流", SUB, (241, 245, 249))
    x = 64
    for label, color in [("插件=工具入口", COL["blue"]), ("Skill=工作流", COL["green"]), ("MCP=外部系统", COL["purple"])]:
        x = chip(draw, x, 610, label, color)
    rounded(draw, [800, 155, 1190, 560], 34, (255, 255, 255), outline=COL["cyan"], width=5)
    icons = [
        ("浏览器", "浏览", COL["blue"]), ("GitHub", "Git", (15, 23, 42)), ("设计", "设计", COL["pink"]),
        ("文档", "文档", COL["blue"]), ("PPT", "PPT", COL["orange"]), ("表格", "表格", COL["green"]),
        ("视频", "视频", COL["purple"]), ("研究", "研究", COL["cyan"]), ("写作", "写作", COL["yellow"]),
    ]
    x0, y0 = 835, 195
    for idx, (name, short, color) in enumerate(icons):
        x = x0 + (idx % 3) * 115
        y = y0 + (idx // 3) * 115
        rounded(draw, [x, y, x + 82, y + 82], 22, color)
        write(draw, (x + 15, y + 22), short, SMALL, COL["white"])
        write(draw, (x - 2, y + 90), name, SMALL, (15, 23, 42))
    canvas.save(imgdir / "05-plugins-skills-cover-cn.jpg", quality=94)


def plugin_vs_skill():
    canvas = Image.new("RGB", (1280, 720), (248, 250, 252))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 1280, 112], fill=COL["navy"])
    write(draw, (54, 30), "插件与 Skill：不要混着用", TITLE)
    cols = [
        (70, "插件 Plugin", "安装新能力入口\n可包含工具、界面、资产\n适合浏览器、GitHub", COL["blue"]),
        (470, "Skill", "把工作流写成说明书\n可带脚本、资料、示例\n适合写稿、PPT、研究、改图", COL["green"]),
        (870, "MCP", "连接外部系统和数据\n提供工具、资源、提示词\n适合 Jira、Linear、文档库", COL["purple"]),
    ]
    for x, title, body, color in cols:
        rounded(draw, [x, 170, x + 340, 525], 28, (255, 255, 255), outline=color, width=5)
        write(draw, (x + 28, 205), title, CARD, (15, 23, 42))
        yy = 275
        for line in body.split("\n"):
            write(draw, (x + 28, yy), line, SMALL, (51, 65, 85))
            yy += 48
    write(draw, (76, 610), "选择顺序：已有插件先装插件；重复流程写成 Skill；需要外部系统就接 MCP。", SUB, (15, 23, 42))
    canvas.save(imgdir / "11-plugin-vs-skill-cn.jpg", quality=94)


def content_workflow():
    canvas = Image.new("RGB", (1280, 720), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 1280, 112], fill=(30, 41, 59))
    write(draw, (54, 30), "内容创作 Skill：把一条内容做成流水线", TITLE)
    steps = [
        ("1 选题研究", "资料收集\n竞品分析\n大纲生成", COL["blue"]),
        ("2 写稿润色", "中文口吻\n去模板腔\n标题优化", COL["pink"]),
        ("3 配图排版", "封面图\n社媒卡片\n公众号图文", COL["orange"]),
        ("4 PPT/视频", "演示稿\n短视频脚本\n字幕切片", COL["purple"]),
        ("5 分发复盘", "平台适配\nSEO\n数据分析", COL["green"]),
    ]
    x = 45
    for idx, (title, body, color) in enumerate(steps):
        card(draw, x, 170, 225, 280, title, body, color)
        if idx < len(steps) - 1:
            draw.line([x + 225, 310, x + 250, 310], fill=(100, 116, 139), width=5)
            draw.polygon([(x + 250, 310), (x + 235, 300), (x + 235, 320)], fill=(100, 116, 139))
        x += 245
    rounded(draw, [70, 580, 1210, 650], 22, (239, 246, 255), outline=COL["blue"], width=2)
    write(draw, (95, 598), "适合沉淀为 Skill 的规则：步骤固定、素材多、需要脚本、每次都要重复做。", SUB, (15, 23, 42))
    canvas.save(imgdir / "12-content-skill-workflow-cn.jpg", quality=94)


hero("03-case-cover-cn.jpg", "04-codex-browser-cn.jpg", "Codex 实战速查", "修 bug、安全检查、高质量提示词，一篇讲透核心用法", [("Debug闭环", COL["orange"]), ("安全检查", COL["green"]), ("提示词模板", COL["blue"])])
hero("04-agents-cover-cn.jpg", "01-codex-app-cn.jpg", "AGENTS.md 深度模板", "把团队规范变成 Codex 每次都会读的上下文", [("项目规则", COL["blue"]), ("完成标准", COL["green"]), ("Review指南", COL["purple"])])
flow_debug()
agents_template()
safety()
cheat()
plugin_skill_cover()
plugin_vs_skill()
content_workflow()

for path in sorted(imgdir.glob("*.jpg")):
    if path.name in {"03-case-cover-cn.jpg", "04-agents-cover-cn.jpg", "05-plugins-skills-cover-cn.jpg", "07-debug-loop-cn.jpg", "08-agents-template-cn.jpg", "09-safety-cn.jpg", "10-cheatsheet-cn.jpg", "11-plugin-vs-skill-cn.jpg", "12-content-skill-workflow-cn.jpg"}:
        print(path.name, path.stat().st_size)
