from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_DIR_RE = re.compile(r"^0[1-6]-")
ARTICLE_FILE_RE = re.compile(r"^\d{2}-.+\.md$")
BAD_CHARS = ["�", "锟", "鐭", "鈥", "Ã", "Â"]
RISKY_CODE_LANGS = {"md", "markdown", "mermaid", ""}

def iter_articles():
    for directory in sorted(p for p in ROOT.iterdir() if p.is_dir() and ARTICLE_DIR_RE.match(p.name)):
        for file in sorted(directory.glob("*.md")):
            if ARTICLE_FILE_RE.match(file.name):
                yield file

def fenced_openers(text):
    for match in re.finditer(r"^(`{3,}|~{3,})([^\n]*)$", text, re.M):
        line_no = text[: match.start()].count("\n") + 1
        yield line_no, match.group(1), match.group(2).strip()

def scan_file(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel = path.relative_to(ROOT)
    problems = []

    if any(ch in text for ch in BAD_CHARS):
        problems.append(("P0", "疑似乱码字符"))
    if "****" in text:
        problems.append(("P1", "存在异常加粗符号 ****"))

    first = next((line.strip() for line in lines if line.strip()), "")
    if first.startswith("# "):
        problems.append(("P0", "正文首行重复 H1 标题"))
    if first and not first.startswith(">"):
        problems.append(("P1", "正文开头不是一句话结论引用"))
    if first.startswith("!"):
        problems.append(("P1", "正文以图片开头，封面应外置"))
    if "文章封面" in text or "%E6%96%87%E7%AB%A0%E5%B0%81%E9%9D%A2" in text:
        problems.append(("P1", "正文包含文章封面图引用，封面应外置"))

    for index, line in enumerate(lines, 1):
        if line.startswith("# "):
            problems.append(("P0", f"第 {index} 行存在 H1"))
        if "点个" in line and "在看" in line:
            problems.append(("P1", f"第 {index} 行存在平台 CTA"))

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
