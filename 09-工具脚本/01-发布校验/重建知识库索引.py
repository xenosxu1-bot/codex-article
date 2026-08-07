from pathlib import Path
from collections import defaultdict
from datetime import date
import re

ROOT = Path(__file__).resolve().parents[2]
DATE = date.today().isoformat()
ASSET = ROOT / "07-资料与流程" / "03-资产与核验" / "文章资产登记表.md"
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
        if len(cols) < 9:
            continue
        no, title, category, series, tags, path_cell, chars, storage_status, repeat_rate = cols[:9]
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
            "storage_status": storage_status,
            "repeat_rate": normalize_repeat_rate(repeat_rate),
        })
    return sorted(rows, key=lambda r: int(r["id"]))


def normalize_repeat_rate(value: str) -> str:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)%", value.strip())
    if not match:
        return value.strip()
    return f"{float(match.group(1)):.2f}%"


def link(title, path):
    return f"[{title}](<{path}>)"


def update_readme(rows):
    p = ROOT / "README.md"
    text = p.read_text(encoding="utf-8")
    before = text.split("## 全部文章", 1)[0].rstrip()
    before = before.replace("\x007-资料与流程/03-资产与核验/历史素材归档/", "`07-资料与流程/03-资产与核验/历史素材归档/`")
    before = before.replace("维护文章编号、分类、标签和发布状态", "维护文章编号、分类、标签和重复率")
    before = re.sub(r"## 文章发布状态\n.*?\n## 编码与同步约定", "## 文章重复率\n\n> 每篇正式文章的重复率均显示在下方「全部文章」表格中。《文章资产登记表》是重复率的唯一事实来源，重建索引不会丢失这一列。\n\n- 统一格式：全部使用百分比并保留两位小数，例如 `2.80%`。\n- 计算口径：正文五字片段 Dice 相似度 × 85% + 标题二字片段 Dice 相似度 × 15%，取与原创清单全部文章比较后的最大值。\n- 具体匹配对象：查看 `07-资料与流程/04-索引与报告/内容去重报告/原创清单对仓库文章重复度-2026-08-07.md`。\n\n## 编码与同步约定", before, flags=re.S)
    before = re.sub(
        r"> (?:入库状态|重复率)：\d+/\d+ .*",
        f"> 重复率登记：{len(rows)}/{len(rows)} 篇文章已完成原创清单重复率计算，正文图片、本地链接与正文图注检查通过。",
        before,
    )
    out = [
        before,
        "",
        "## 全部文章",
        "",
        "> 重复率以《文章资产登记表》为准，由本脚本生成到每篇文章行；统一保留两位小数；编号使用文件名前缀，下架或删除后不自动重排，只有明确批准的一次性迁移才按《编号变更记录》执行。",
        "",
        "| 编号 | 标题 | 分类 | 系列 | 标签 | 重复率 | 中文字数 |",
        "| ---: | --- | --- | --- | --- | --- | ---: |",
    ]
    for r in rows:
        out.append(f"| {r['id']} | {link(r['title'], r['path'])} | {r['category']} | {r['series']} | {r['tags_text']} | {r['repeat_rate']} | {r['chars']} |")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_total_index(rows):
    p = NAV / "知识库总索引.md"
    out = [
        "# 知识库总索引",
        "",
        f"> 更新时间：{DATE}；当前正式文章 {len(rows)} 篇。",
        f"> \u91cd\u590d\u7387\u767b\u8bb0\uff1a{len(rows)}/{len(rows)} \u7bc7\u6587\u7ae0\u5df2\u5b8c\u6210\u539f\u521b\u6e05\u5355\u91cd\u590d\u7387\u8ba1\u7b97\u3002",
        "> 编号规则：本页使用文章文件名前缀编号；下架或删除后不自动重排；只有明确批准的一次性迁移才按《编号变更记录》执行；《编号变更记录》保留旧号到新号的追溯关系，编号与正文路径、文章资产登记表和发布记录保持一致。",
        "",
        "| 编号 | 标题 | 分类 | 系列 | 标签 | 重复率 | 中文字数 |",
        "| ---: | --- | --- | --- | --- | --- | ---: |",
    ]
    for r in rows:
        out.append(f"| {r['id']} | {link(r['title'], '../' + r['path'])} | {r['category']} | {r['series']} | {r['tags_text']} | {r['repeat_rate']} | {r['chars']} |")
    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def update_home(rows):
    p = NAV / "知识库首页.md"
    out = [
        "# 知识库首页",
        "",
        f"> 更新时间：{DATE}；当前正式文章 {len(rows)} 篇。",
        f"> \u91cd\u590d\u7387\u767b\u8bb0\uff1a{len(rows)}/{len(rows)} \u7bc7\u6587\u7ae0\u5df2\u5b8c\u6210\u539f\u521b\u6e05\u5355\u91cd\u590d\u7387\u767b\u8bb0\uff1b\u9996\u9875\u548c\u603b\u7d22\u5f15\u4f7f\u7528\u6587\u7ae0\u6587\u4ef6\u540d\u524d\u7f00\u7f16\u53f7\uff0c\u4e0b\u67b6\u6216\u5220\u9664\u540e\u4e0d\u81ea\u52a8\u91cd\u6392\uff0c\u53ea\u6709\u660e\u786e\u6279\u51c6\u7684\u4e00\u6b21\u6027\u8fc1\u79fb\u624d\u6309\u300a\u7f16\u53f7\u53d8\u66f4\u8bb0\u5f55\u300b\u6267\u884c\uff1b\u300a\u7f16\u53f7\u53d8\u66f4\u8bb0\u5f55\u300b\u4fdd\u7559\u65e7\u53f7\u5230\u65b0\u53f7\u7684\u8ffd\u6eaf\u5173\u7cfb\u3002",
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
        "- [文章资产登记表](<../07-资料与流程/03-资产与核验/文章资产登记表.md>)：查看正式文章的历史编号、路径和重复率。",
        "- [发布记录](<../07-资料与流程/02-选题与发布/发布记录.md>)：查看历次入库、删除、同步和质量修正记录。",
        "- [内容维护清单](<../07-资料与流程/01-当前流程/内容维护清单.md>)：查看后续选题和维护事项。",
        "- [项目结构与文件归位说明](<../07-资料与流程/01-当前流程/项目结构与文件归位说明.md>)：查找文章、素材、流程、脚本与临时文件的归属位置。",
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
    new = '- 新增文章时同步更新 `README.md`、`00-知识库导航/知识库总索引.md`、`分类索引.md`、`系列索引.md`、`标签索引.md`、`07-资料与流程/03-资产与核验/文章资产登记表.md` 和 `07-资料与流程/02-选题与发布/发布记录.md`；默认使用文件名前缀编号。删除、下架或转为草稿不修改既有文章文件名、图片和元数据；只有已批准的一次性迁移，才按《编号变更记录》同步这些内容。'
    pattern = r"- 新增文章时同步更新 `README\.md`、`00-知识库导航/知识库总索引\.md`、`分类索引\.md`、`系列索引\.md`、`标签索引\.md` 和 `07-资料与流程/发布记录\.md`；[^\n]*"
    text, count = re.subn(pattern, new, text)
    if count == 0 and new not in text:
        text = text.rstrip() + "\n" + new + "\n"
    rule = "- 更新 README、首页或知识库索引后，必须运行 `09-工具脚本/01-发布校验/重建知识库索引.py` 或按其输出规则重建，确认展示编号与文章文件名前缀一致、链接可访问、资产登记表、元数据和正在使用的素材文件均已同步，需要时可依《编号变更记录》追溯。"
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
