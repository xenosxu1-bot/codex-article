# -*- coding: utf-8 -*-
"""生成“选题文章绑定表”。

用途：把 07-资料与流程/选题库.md 中的选题ID，和
07-资料与流程/文章资产登记表.md 中已经生成的正文文件建立绑定，
用于查重、排期和避免重复生成同主题文章。
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC_FILE = ROOT / "07-资料与流程" / "选题库.md"
ASSET_FILE = ROOT / "07-资料与流程" / "文章资产登记表.md"
OUTPUT_FILE = ROOT / "07-资料与流程" / "选题文章绑定表.md"


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.split("|")[1:-1]]


def parse_topics(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if re.match(r"^\| T\d+ \|", line):
            c = split_row(line)
            if len(c) >= 10:
                rows.append({
                    "id": c[0], "title": c[1], "category": c[2], "series": c[3],
                    "audience": c[4], "question": c[5], "deliverable": c[6],
                    "refs": c[7], "priority": c[8], "status": c[9],
                })
    return rows


def parse_assets(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if re.match(r"^\| \d+ \|", line):
            c = split_row(line)
            if len(c) >= 8:
                path_match = re.search(r"`([^`]+)`", c[5])
                rows.append({
                    "no": c[0], "title": c[1], "category": c[2], "series": c[3],
                    "tags": c[4], "path": path_match.group(1) if path_match else c[5],
                    "words": c[6], "status": c[7],
                })
    return rows


def normalize(text: str) -> str:
    return re.sub(r"[\s`~!@#$%^&*()_+\-=\[\]{};:'\"\\|,.<>/?，。、“”‘’：；（）【】《》？！·+—-]", "", text.lower())


def grams(text: str) -> set[str]:
    return {text[i:i + 2] for i in range(max(0, len(text) - 1))}


def similarity(a: str, b: str) -> float:
    a = normalize(a)
    b = normalize(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return min(0.92, min(len(a), len(b)) / max(len(a), len(b)) + 0.25)
    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    inter = len(ga & gb)
    return inter / (len(ga) + len(gb) - inter)


def parse_refs(refs: str) -> list[str]:
    return [str(int(x)) for x in re.findall(r"\d+", refs or "")]


def link_asset(asset: dict[str, str] | None) -> str:
    if not asset:
        return "—"
    href = "../" + asset["path"].replace(" ", "%20")
    return f"[{asset['no']} {asset['title']}]({href})"


def raw_asset_path(asset: dict[str, str] | None) -> str:
    if not asset:
        return "—"
    return f"`{asset['path']}`"


def main() -> None:
    topics = parse_topics(TOPIC_FILE.read_text(encoding="utf-8"))
    assets = parse_assets(ASSET_FILE.read_text(encoding="utf-8"))
    asset_by_no = {str(int(a["no"])): a for a in assets}
    asset_by_title = {a["title"]: a for a in assets}

    exact_bindings = []
    candidate_bindings = []
    invalid_refs = []
    topic_status = []

    for topic in topics:
        exact = asset_by_title.get(topic["title"])
        refs = parse_refs(topic["refs"])
        valid = [no for no in refs if no in asset_by_no]
        invalid = [no for no in refs if no not in asset_by_no]
        if invalid:
            invalid_refs.append({"topic": topic, "valid": valid, "invalid": invalid})

        scored = sorted(
            ({"asset": asset, "score": similarity(topic["title"], asset["title"])} for asset in assets),
            key=lambda item: item["score"],
            reverse=True,
        )
        top = scored[0] if scored else None
        bind_type = "未生成"
        bound = []
        if exact:
            bind_type = "已生成"
            bound = [exact]
            exact_bindings.append({"topic": topic, "asset": exact})
        elif top and top["score"] >= 0.35:
            bind_type = "疑似重复/可合并"
            bound = [top["asset"]]
            candidate_bindings.append({"topic": topic, "asset": top["asset"], "score": top["score"]})
        elif valid:
            bind_type = "关联旧文"
            bound = [asset_by_no[no] for no in valid]

        topic_status.append({
            "topic": topic, "bind_type": bind_type, "bound": bound,
            "valid_refs": valid, "invalid_refs": invalid,
        })

    category_count: dict[str, int] = {}
    series_count: dict[str, int] = {}
    for asset in assets:
        category_count[asset["category"]] = category_count.get(asset["category"], 0) + 1
        series_count[asset["series"]] = series_count.get(asset["series"], 0) + 1

    lines: list[str] = []
    lines.append("# 选题文章绑定表")
    lines.append("")
    lines.append(f"> 更新时间：{date.today().isoformat()}")
    lines.append("> 作用：把 `选题库.md` 中的选题ID，与已经生成/入库的正文文件绑定，方便查看状态，避免把同一主题重复写成多篇文章。")
    lines.append("> 数据来源：`选题库.md`、`文章资产登记表.md`。")
    lines.append("")
    lines.append("## 一、当前状态概览")
    lines.append("")
    lines.append(f"- 正式文章：{len(assets)} 篇。")
    lines.append(f"- 选题库候选：{len(topics)} 条。")
    lines.append(f"- 已精确绑定生成文件：{len(exact_bindings)} 条。")
    lines.append(f"- 疑似已覆盖/可合并选题：{len(candidate_bindings)} 条。")
    invalid_note = "需要后续清理" if invalid_refs else "无须清理"
    lines.append(f"- 关联编号失效项：{len(invalid_refs)} 条，{invalid_note}。")
    lines.append("")
    lines.append("## 二、绑定规则")
    lines.append("")
    lines.append("1. 新增选题时，先查本表和 `文章资产登记表.md`，确认没有同题、同核心问题、同交付物。")
    lines.append("2. 进入写作后，在选题库状态中保留选题ID；正式入库后，在本表补齐正式编号和正文路径。")
    lines.append("3. 如果新选题只是旧文的更新版、案例版或模板版，状态应标为“可合并/更新”，不要直接生成新文章。")
    lines.append("4. `关联已发布` 只能引用 `文章资产登记表.md` 中存在的正式编号；失效编号要清理或改写为当前正式编号。")
    lines.append("")
    lines.append("## 三、选题 → 已生成文件状态")
    lines.append("")
    lines.append("| 选题ID | 暂定标题 | 选题状态 | 绑定状态 | 绑定文章/路径 | 去重提示 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for item in topic_status:
        topic = item["topic"]
        bound = "<br>".join(link_asset(asset) for asset in item["bound"]) if item["bound"] else "—"
        hint = "可继续排期，写作前仍需查重"
        if item["bind_type"] == "已生成":
            hint = "已生成正文，后续只做修订或更新，不再重复生成"
        elif item["bind_type"] == "疑似重复/可合并":
            hint = "与 " + "、".join(asset["no"] for asset in item["bound"]) + " 主题接近，建议改为更新版/案例版或合并"
        elif item["invalid_refs"]:
            hint = "关联编号含失效项：" + "、".join(item["invalid_refs"]) + "，写作前先校准引用"
        elif item["valid_refs"]:
            hint = "已有相关旧文：" + "、".join(item["valid_refs"]) + "，正文需明确新增角度"
        lines.append(f"| {topic['id']} | {topic['title']} | {topic['status']} | {item['bind_type']} | {bound} | {hint} |")
    lines.append("")
    lines.append("## 四、已生成文章 → 选题绑定")
    lines.append("")
    lines.append("| 编号 | 已生成文章 | 正文路径 | 绑定选题ID | 说明 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for asset in assets:
        exact = next((b for b in exact_bindings if b["asset"]["no"] == asset["no"]), None)
        candidates = [b for b in candidate_bindings if b["asset"]["no"] == asset["no"]]
        ids = []
        if exact:
            ids.append(exact["topic"]["id"])
        ids.extend(f"{b['topic']['id']}（疑似）" for b in candidates)
        note = "历史文章，暂未绑定选题ID"
        if exact:
            note = "已由选题库生成/入库"
        elif candidates:
            note = "已有候选选题与本文主题接近，生成前需改角度"
        lines.append(f"| {asset['no']} | {asset['title']} | {raw_asset_path(asset)} | {'、'.join(ids) if ids else '—'} | {note} |")
    lines.append("")
    lines.append("## 五、关联编号失效清单")
    lines.append("")
    if invalid_refs:
        lines.append("| 选题ID | 暂定标题 | 有效关联 | 失效编号 | 处理建议 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in invalid_refs:
            topic = item["topic"]
            lines.append(f"| {topic['id']} | {topic['title']} | {'、'.join(item['valid']) if item['valid'] else '—'} | {'、'.join(item['invalid'])} | 对照文章资产登记表改成现有编号，或删除无效关联。 |")
    else:
        lines.append("当前没有失效关联编号。")
    lines.append("")
    lines.append("## 六、正式文章分布")
    lines.append("")
    lines.append("分类分布：")
    for key, value in sorted(category_count.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"- {key}：{value} 篇")
    lines.append("")
    lines.append("系列分布：")
    for key, value in sorted(series_count.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"- {key}：{value} 篇")
    lines.append("")
    lines.append("## 七、每次生成新文章后的更新动作")
    lines.append("")
    lines.append("1. 在 `文章资产登记表.md` 登记正式编号、标题、分类、系列、标签和正文路径。")
    lines.append("2. 在 `选题库.md` 把对应选题状态改到 `S6 已入库` 或 `S7 已复盘`。")
    lines.append("3. 重新运行绑定检查，刷新本表。")
    lines.append("4. 如果发现疑似重复，先决定“修订旧文、合并选题、改成新角度”，再生成正文。")

    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"已生成：{OUTPUT_FILE.relative_to(ROOT)}")
    print(f"正式文章：{len(assets)}；候选选题：{len(topics)}；精确绑定：{len(exact_bindings)}；疑似重复：{len(candidate_bindings)}；失效关联：{len(invalid_refs)}")


if __name__ == "__main__":
    main()
