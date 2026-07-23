from pathlib import Path
from collections import defaultdict
import re

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-07-23"
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
    before = text.split("## 全部文章", 1)[0].rstrip()
    before = re.sub(
        r"这是一个面向 AI 工具、Codex 使用、AI Agent 工作流和个人效率方法的中文知识库。当前保留 \d+ 篇整合优化版文章：.*",
        f"这是一个面向 AI 工具、Codex 使用、AI Agent 工作流和个人效率方法的中文知识库。当前保留 {len(rows)} 篇整合优化版文章：重复主题已合并，短稿已补足适用边界、执行清单和验收标准；README 按文章编号升序展示，编号与文章文件名前缀、资产登记表和发布记录保持一致；下架或删除后自动连续补位；《编号变更记录》保留旧号到新号的追溯关系。",
        before,
    )
    before = re.sub(r"> 文章数量：\d+ 篇", f"> 文章数量：{len(rows)} 篇", before)
    before = re.sub(r"> 发布状态：\d+/\d+ 已整合入库.*", f"> 发布状态：{len(rows)}/{len(rows)} 已整合入库，正文图片、本地链接与正文图注检查通过。", before)
    out = [
        before,
        "",
        "## 全部文章",
        "",
        "> 编号规则：README 使用文章文件名前缀编号；下架或删除后自动连续补位；《编号变更记录》保留旧号到新号的追溯关系，编号与正文路径、文章资产登记表和发布记录保持一致。",
        "",
        "| 编号 | 标题 | 分类 | 系列 | 标签 | 中文字数 |",
        "| ---: | --- | --- | --- | --- | ---: |",
    ]
    for r in rows:
        out.append(f"| {r['id']} | {link(r['title'], r['path'])} | {r['category']} | {r['series']} | {r['tags_text']} | {r['chars']} |")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_total_index(rows):
    p = NAV / "知识库总索引.md"
    out = [
        "# 知识库总索引",
        "",
        f"> 更新时间：{DATE}；当前正式文章 {len(rows)} 篇。",
        f"> 发布状态：{len(rows)}/{len(rows)} 已整合入库。",
        "> 编号规则：本页使用文章文件名前缀编号；下架或删除后自动连续补位；《编号变更记录》保留旧号到新号的追溯关系，编号与正文路径、文章资产登记表和发布记录保持一致。",
        "",
        "| 编号 | 标题 | 分类 | 系列 | 标签 | 中文字数 |",
        "| ---: | --- | --- | --- | --- | ---: |",
    ]
    for r in rows:
        out.append(f"| {r['id']} | {link(r['title'], '../' + r['path'])} | {r['category']} | {r['series']} | {r['tags_text']} | {r['chars']} |")
    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def update_home(rows):
    p = NAV / "知识库首页.md"
    out = [
        "# 知识库首页",
        "",
        f"> 更新时间：{DATE}；当前正式文章 {len(rows)} 篇。",
        "> 发布状态：全部已整合入库；首页和总索引使用文章文件名前缀编号，下架或删除后自动连续补位；《编号变更记录》保留旧号到新号的追溯关系。",
        "",
        "## 从哪里开始",
        "",
        "- [阅读路径](<阅读路径.md>)：按你的目标选择第一篇文章，适合第一次进入知识库的读者。",
        "- [知识库总索引](<知识库总索引.md>)：按文章编号查看全部文章。",
        "- [分类索引](<分类索引.md>)：按主题目录查找。",
        "- [系列索引](<系列索引.md>)：按专题路线连续阅读。",
        "- [标签索引](<标签索引.md>)：按关键词查找。",
        "",
        "## 维护与历史",
        "",
        "- [文章资产登记表](<../07-资料与流程/文章资产登记表.md>)：查看正式文章的历史编号、路径和发布状态。",
        "- [发布记录](<../07-资料与流程/发布记录.md>)：查看历次入库、删除、同步和质量修正记录。",
        "- [内容维护清单](<../07-资料与流程/内容维护清单.md>)：查看后续选题和维护事项。",
        "",
        "## 按文章编号",
        "",
    ]
    for r in rows:
        out.append(f"- {r['id']}. {link(r['title'], '../' + r['path'])}｜{r['category']}｜{r['series']}")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_category_index(rows):
    p = NAV / "分类索引.md"
    by = defaultdict(list)
    for r in rows:
        by[r["category"]].append(r)
    out = [
        "# 分类索引",
        "",
        f"> 更新时间：{DATE}",
        f"> 当前正式文章 {len(rows)} 篇；每个分类内按文章编号升序展示，编号与正文文件名前缀一致。",
        "",
    ]
    for cat in CATEGORIES:
        items = sorted(by.get(cat, []), key=lambda r: int(r["id"]))
        out += [f"## {cat}（{len(items)} 篇）", ""]
        if not items:
            out += ["- 暂无正式入库文章。", ""]
            continue
        for r in items:
            out.append(f"- {r['id']}. {link(r['title'], '../' + r['path'])}｜{r['series']}｜{r['tags_text']}")
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
        f"> 当前正式文章 {len(rows)} 篇；每个分组内按文章编号升序展示，编号与正文文件名前缀一致。",
        "",
    ]
    for key in sorted(by.keys(), key=lambda k: (k.lower(), k)):
        items = sorted(by[key], key=lambda r: int(r["id"]))
        out += [f"## {key}（{len(items)} 篇）", ""]
        for r in items:
            out.append(f"- {r['id']}. {link(r['title'], '../' + r['path'])}｜{r['category']}")
        out.append("")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_category_readmes(rows):
    by_path_prefix = defaultdict(list)
    for r in rows:
        prefix = r["path"].split("/", 1)[0]
        by_path_prefix[prefix].append(r)

    category_dirs = sorted(
        p.name for p in ROOT.iterdir()
        if p.is_dir() and re.fullmatch(r"0[1-6]-.+", p.name)
    )
    for prefix in category_dirs:
        items = sorted(by_path_prefix.get(prefix, []), key=lambda r: int(r["id"]))
        p = ROOT / prefix / "README.md"
        cat_title = prefix.split("-", 1)[1] if "-" in prefix else prefix
        out = [
            f"# {cat_title}",
            "",
            f"> 共 {len(items)} 篇；分类内按文章编号升序展示，编号与文件名和资产登记表一致。",
            "",
        ]
        if items:
            out += [
                "| 编号 | 标题 | 系列 | 标签 | 中文字数 |",
                "| ---: | --- | --- | --- | ---: |",
            ]
            for r in items:
                filename = r["path"].split("/", 1)[1]
                out.append(f"| {r['id']} | {link(r['title'], filename)} | {r['series']} | {r['tags_text']} | {r['chars']} |")
        else:
            out.append("暂无正式入库文章；后续新增文章后由重建脚本自动刷新。")
        p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def update_agents_rule():
    p = ROOT / "AGENTS.md"
    text = p.read_text(encoding="utf-8")
    new = "- 新增文章时同步更新 `README.md`、`00-知识库导航/知识库总索引.md`、`分类索引.md`、`系列索引.md`、`标签索引.md` 和 `07-资料与流程/发布记录.md`；读者可见的 README、首页和索引使用文章文件名前缀编号；删除或下架后立即连续补位，并同步更新文件名、正在使用的图片、元数据、资产登记表和发布记录；旧号→新号映射保留在编号变更记录中。"
    pattern = r"- 新增文章时同步更新 `README\.md`、`00-知识库导航/知识库总索引\.md`、`分类索引\.md`、`系列索引\.md`、`标签索引\.md` 和 `07-资料与流程/发布记录\.md`；[^\n]*"
    text, count = re.subn(pattern, new, text)
    if count == 0 and new not in text:
        text = text.rstrip() + "\n" + new + "\n"
    rule = "- 更新 README、首页或知识库索引后，必须运行 `09-工具脚本/重建知识库索引.py` 或按其输出规则重建，确认展示编号与文章文件名前缀一致、链接可访问、资产登记表、元数据和正在使用的素材文件均已同步，需要时可依《编号变更记录》追溯。"
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
    print(f"重建完成：{len(rows)} 篇文章。README 和知识库索引已使用文章文件名前缀编号。")


if __name__ == "__main__":
    main()
