from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_DIR_RE = re.compile(r"^0[1-6]-")
ARTICLE_FILE_RE = re.compile(r"^\d{2}-.+\.md$")
BAD_CHARS = ["�", "锟", "鐭", "鈥", "Ã", "Â"]
RISKY_CODE_LANGS = {"md", "markdown", "mermaid", ""}
PUBLIC_TAIL_HEADINGS = ("图片来源", "图片来源与发布提醒", "审核记录", "参考资料", "资料来源", "发布检查", "来源与发布")
INTERNAL_REMINDERS = ("发布前请", "请再次核验", "发布到公众号或商业渠道前", "建议发布前")
BROAD_UNSOURCED_PHRASES = ("当前一些产品", "产品方公开资料也会", "官方安全建议会专门")
FINAL_CHECK_SENTENCE = "本文发布前已完成事实、版权与格式检查。"


def iter_articles():
    for directory in sorted(p for p in ROOT.iterdir() if p.is_dir() and ARTICLE_DIR_RE.match(p.name)):
        for file in sorted(directory.glob("*.md")):
            if ARTICLE_FILE_RE.match(file.name):
                yield file


def fenced_openers(text):
    for match in re.finditer(r"^(`{3,}|~{3,})([^\n]*)$", text, re.M):
        line_no = text[: match.start()].count("\n") + 1
        yield line_no, match.group(1), match.group(2).strip()


def find_tables(lines):
    separator_re = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and separator_re.match(lines[i + 1]):
            start = i + 1
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            headers = [cell.strip() for cell in block[0].strip().strip("|").split("|")]
            rows = max(0, len(block) - 2)
            yield start, len(headers), rows, block[0]
        else:
            i += 1


def scan_file(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel = path.relative_to(ROOT)
    problems = []

    if any(ch in text for ch in BAD_CHARS):
        problems.append(("P0", "疑似乱码字符"))
    if "****" in text:
        problems.append(("P1", "存在异常加粗符号 ****"))
    if re.search(r"\[\^\d+\]", text):
        problems.append(("P1", "正文含脚注标记；公众号版请改为正文表达或外置来源说明"))
    if any(line.startswith("## ") and any(heading in line for heading in PUBLIC_TAIL_HEADINGS) for line in lines):
        problems.append(("P1", "正文含图片来源/审核记录/参考资料等内部区块"))
    if any(reminder in text for reminder in INTERNAL_REMINDERS):
        problems.append(("P1", "正文含发布前复核提醒；应移至资产登记表或发布流程"))
    if any(phrase in text for phrase in BROAD_UNSOURCED_PHRASES):
        problems.append(("P1", "存在过实的泛化产品/官方表述；请改为有边界的类别表达"))

    first = next((line.strip() for line in lines if line.strip()), "")
    if first.startswith("# "):
        problems.append(("P0", "正文首行重复 H1 标题"))
    if first and not first.startswith(">"):
        problems.append(("P1", "正文开头不是一句话结论引用"))
    if first.startswith("!"):
        problems.append(("P1", "正文以图片开头，封面应外置"))
    if "文章封面" in text or "%E6%96%87%E7%AB%A0%E5%B0%81%E9%9D%A2" in text:
        problems.append(("P1", "正文包含文章封面图引用，封面应外置"))
    if FINAL_CHECK_SENTENCE not in text:
        problems.append(("P1", "正文缺少统一发布检查收束句"))

    in_fence = False
    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
        if in_fence:
            continue
        if line.startswith("# "):
            problems.append(("P0", f"第 {index} 行存在 H1"))
        if "点个" in line and "在看" in line:
            problems.append(("P1", f"第 {index} 行存在平台 CTA"))
        if re.search(r"\S\s+#{2,6}\s+", line):
            problems.append(("P1", f"第 {index} 行疑似标题与正文挤在同一行"))
        if re.search(r"!\[[^\]]*\]\([^)]+\)\S", line):
            problems.append(("P1", f"第 {index} 行疑似图片与正文挤在同一行"))

    bold_count = len(re.findall(r"\*\*[^*]+\*\*", text))
    if bold_count > 10:
        problems.append(("P1", f"加粗 {bold_count} 处，超过 10 处"))
    elif bold_count > 6:
        problems.append(("P2", f"加粗 {bold_count} 处，建议继续收敛"))

    openers = list(fenced_openers(text))
    if len(openers) % 2 != 0:
        problems.append(("P0", "代码块数量疑似未闭合"))
    for idx, (line_no, fence, lang) in enumerate(openers):
        if idx % 2 == 0:
            normalized = lang.lower()
            if normalized in RISKY_CODE_LANGS or "`" in normalized:
                problems.append(("P1", f"第 {line_no} 行存在发布风险代码块语言：{lang or '无语言'}"))
            if fence != "```":
                problems.append(("P1", f"第 {line_no} 行存在非标准代码围栏：{fence}"))

    for line_no, cols, rows, header in find_tables(lines):
        if cols >= 4:
            problems.append(("P1", f"第 {line_no} 行存在 {cols} 列宽表格；公众号移动端请改成卡片/小节"))

    if "？" in path.name:
        problems.append(("P1", "文件名包含问号"))

    return rel, problems


def main():
    total = 0
    counts = {"P0": 0, "P1": 0, "P2": 0}
    for article in iter_articles():
        total += 1
        rel, problems = scan_file(article)
        if not problems:
            continue
        print(f"\n{rel}")
        for level, message in problems:
            counts[level] += 1
            print(f"  [{level}] {message}")
    print(f"\n扫描文章：{total} 篇")
    print(f"P0: {counts['P0']}  P1: {counts['P1']}  P2: {counts['P2']}")
    return 1 if counts["P0"] or counts["P1"] else 0


if __name__ == "__main__":
    sys.exit(main())
