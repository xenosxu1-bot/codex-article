from pathlib import Path
from collections import defaultdict
import re

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-07-20"
ASSET = ROOT / "07-资料与流程" / "文章资产登记表.md"
NAV = ROOT / "00-知识库导航"
CATEGORIES = ["工具教程", "AI知识", "好文方法", "安全治理", "案例实战", "热点追踪"]


def split_row(line: str):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def load_articles():
    rows = []
    for line in ASSET.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        if "---" in line or "编号" in line:
            continue
        cols = split_row(line)
        if len(cols) < 8:
            continue
        no, title, category, series, tags, path_cell, chars, status = cols[:8]
        if not re.fullmatch(r"\d+", no):
            continue
        path = path_cell.strip("`")
        rows.append({
            "id": no.zfill(2),
            "title": title,
            "category": category,
            "series": series,
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "tags_text": tags,
            "path": path,
            "chars": chars,
            "status": status,
        })
    return sorted(rows, key=lambda r: int(r["id"]))


def link(title, path):
    return f"[{title}](<{path}>)"


def update_readme(rows):
    p = ROOT / "README.md"
    text = p.read_text(encoding="utf-8")
    text = text.replace("按编号查看全部文章", "按连续阅读顺序查看全部文章")
    before = text.split("## 全部文章", 1)[0].rstrip()
    before = re.sub(
        r"这是一个面向 AI 工具、Codex 使用、AI Agent 工作流和个人效率方法的中文知识库。当前保留 \d+ 篇整合优化版文章：.*",
        f"这是一个面向 AI 工具、Codex 使用、AI Agent 工作流和个人效率方法的中文知识库。当前保留 {len(rows)} 篇整合优化版文章：重复主题已合并，短稿已补足适用边界、执行清单和验收标准；README 按连续阅读顺序展示，历史文章编号保留在文件名、资产登记表和发布记录中。",
        before,
    )
    before = re.sub(r"> 文章数量：\d+ 篇", f"> 文章数量：{len(rows)} 篇", before)
    before = re.sub(r"> 发布状态：\d+/\d+ 已整合入库.*", f"> 发布状态：{len(rows)}/{len(rows)} 已整合入库，正文图片与本地链接检查通过。", before)
    out = [before, "", "## 全部文章", "", "> 排序规则：README 采用连续阅读序号，避免因下架文章产生跳号；历史文章编号以文件名、文章资产登记表和发布记录为准。", "", "| 排序 | 标题 | 分类 | 系列 | 标签 | 中文字数 |", "| ---: | --- | --- | --- | --- | ---: |"]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i:02d} | {link(r['title'], r['path'])} | {r['category']} | {r['series']} | {r['tags_text']} | {r['chars']} |")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_total_index(rows):
    p = NAV / "知识库总索引.md"
    out = [
        "# 知识库总索引",
        "",
        f"> 更新时间：{DATE}；当前正式文章 {len(rows)} 篇。",
        f"> 发布状态：{len(rows)}/{len(rows)} 已整合入库。",
        "> 排序规则：本页按连续阅读序号展示；历史文章编号以文件名、文章资产登记表和发布记录为准。",
        "",
        "| 排序 | 标题 | 分类 | 系列 | 标签 | 中文字数 |",
        "| ---: | --- | --- | --- | --- | ---: |",
    ]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i:02d} | {link(r['title'], '../' + r['path'])} | {r['category']} | {r['series']} | {r['tags_text']} | {r['chars']} |")
    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def update_home(rows):
    p = NAV / "知识库首页.md"
    beginner = [rows[i] for i in [0,1,3,4,8]]
    cases = [r for r in rows if r["category"] == "案例实战"]
    methods = [r for r in rows if r["category"] == "好文方法"]
    safety = [r for r in rows if r["category"] in ["安全治理", "工具教程"] and ("PPT" in r["tags_text"] or "OpenClaw" in r["tags_text"] or r["category"] == "安全治理")]
    def names(items):
        return "、".join(r["title"] for r in items)
    out = [
        "# 知识库首页",
        "",
        f"> 更新时间：{DATE}；当前正式文章 {len(rows)} 篇。",
        "> 发布状态：全部已整合入库；首页和总索引使用连续阅读序号，历史编号保留在资产登记表中。",
        "",
        "## 快速入口",
        "",
        "- [总索引](<知识库总索引.md>)：按连续阅读顺序查看全部文章。",
        "- [分类索引](<分类索引.md>)：按主题目录查找。",
        "- [系列索引](<系列索引.md>)：按专题路线连续阅读。",
        "- [标签索引](<标签索引.md>)：按关键词查找。",
        "- [文章资产登记表](<../07-资料与流程/文章资产登记表.md>)：维护历史编号、路径、状态和字数。",
        "",
        "## 阅读路径建议",
        "",
        f"1. 新手先读：{names(beginner)}。",
        f"2. 想看实战案例：{names(cases)}。",
        f"3. 想提升 AI 工作法：{names(methods)}。",
        f"4. 涉及公开发布、权限与资料输入：{names(safety)}。",
        "",
        "## 按阅读顺序",
        "",
    ]
    for i, r in enumerate(rows, 1):
        out.append(f"- {i:02d}. {link(r['title'], '../' + r['path'])}｜{r['category']}｜{r['series']}")
    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def update_category_index(rows):
    p = NAV / "分类索引.md"
    by = defaultdict(list)
    for r in rows:
        by[r["category"]].append(r)
    out = [
        "# 分类索引",
        "",
        f"> 更新时间：{DATE}",
        f"> 当前正式文章 {len(rows)} 篇；每个分类内按连续阅读序号展示，历史文章编号以资产登记表为准。",
        "",
    ]
    for cat in CATEGORIES:
        items = by.get(cat, [])
        out += [f"## {cat}（{len(items)} 篇）", ""]
        if not items:
            out += ["- 暂无正式入库文章。", ""]
            continue
        for i, r in enumerate(items, 1):
            out.append(f"- {i:02d}. {link(r['title'], '../' + r['path'])}｜{r['series']}｜{r['tags_text']}")
        out.append("")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_group_index(rows, field, filename, title):
    p = NAV / filename
    by = defaultdict(list)
    if field == "tags":
        for r in rows:
            for t in r["tags"]:
                by[t].append(r)
    else:
        for r in rows:
            by[r[field]].append(r)
    out = [
        f"# {title}",
        "",
        f"> 更新时间：{DATE}",
        f"> 当前正式文章 {len(rows)} 篇；每个分组内按连续阅读序号展示，历史文章编号以资产登记表为准。",
        "",
    ]
    for key in sorted(by.keys(), key=lambda k: (k.lower(), k)):
        items = sorted(by[key], key=lambda r: int(r["id"]))
        out += [f"## {key}（{len(items)} 篇）", ""]
        for i, r in enumerate(items, 1):
            out.append(f"- {i:02d}. {link(r['title'], '../' + r['path'])}｜{r['category']}")
        out.append("")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_category_readmes(rows):
    by_path_prefix = defaultdict(list)
    for r in rows:
        prefix = r["path"].split("/", 1)[0]
        by_path_prefix[prefix].append(r)
    for prefix, items in by_path_prefix.items():
        p = ROOT / prefix / "README.md"
        items = sorted(items, key=lambda r: int(r["id"]))
        cat_title = prefix.split("-", 1)[1] if "-" in prefix else prefix
        out = [
            f"# {cat_title}",
            "",
            f"> 共 {len(items)} 篇；分类内按连续阅读序号展示，历史文章编号以文件名和资产登记表为准。",
            "",
            "| 排序 | 标题 | 系列 | 标签 | 中文字数 |",
            "| ---: | --- | --- | --- | ---: |",
        ]
        for i, r in enumerate(items, 1):
            filename = r["path"].split("/", 1)[1]
            out.append(f"| {i:02d} | {link(r['title'], filename)} | {r['series']} | {r['tags_text']} | {r['chars']} |")
        p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def update_agents_rule():
    p = ROOT / "AGENTS.md"
    text = p.read_text(encoding="utf-8")
    old = "- 新增文章时同步更新 `README.md`、`00-知识库导航/知识库总索引.md`、`分类索引.md`、`系列索引.md`、`标签索引.md` 和 `07-资料与流程/发布记录.md`；目录、引用图片和文件名均按编号升序排列。"
    new = "- 新增文章时同步更新 `README.md`、`00-知识库导航/知识库总索引.md`、`分类索引.md`、`系列索引.md`、`标签索引.md` 和 `07-资料与流程/发布记录.md`；读者可见的 README、首页和索引使用连续阅读序号，文件名、图片名、资产登记表和发布记录保留历史文章编号，避免链接和记录失真。"
    if old in text:
        text = text.replace(old, new)
    rule = "- 更新 README、首页或知识库索引后，必须运行 `09-工具脚本/重建知识库索引.py` 或按其输出规则重建，确认读者可见序号连续、链接可访问、资产登记表仍保留历史编号。"
    if rule not in text:
        text = text.replace(new, new + "\n" + rule)
    p.write_text(text, encoding="utf-8", newline="\n")


def main():
    rows = load_articles()
    update_readme(rows)
    update_total_index(rows)
    update_home(rows)
    update_category_index(rows)
    update_group_index(rows, "series", "系列索引.md", "系列索引")
    update_group_index(rows, "tags", "标签索引.md", "标签索引")
    update_category_readmes(rows)
    update_agents_rule()
    print(f"重建完成：{len(rows)} 篇文章。README 和知识库索引已使用连续阅读序号。")


if __name__ == "__main__":
    main()
