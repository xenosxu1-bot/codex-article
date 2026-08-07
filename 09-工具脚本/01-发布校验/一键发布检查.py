# -*- coding: utf-8 -*-
"""一键发布前检查。

用途：减少手工串联检查的时间。默认只做检查与必要的索引/绑定表重建，不自动提交、不自动推送。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "09-工具脚本"
ARTICLE_DIR_RE = re.compile(r"^0[1-6]-")
ARTICLE_FILE_RE = re.compile(r"^\d{2}-.+\.md$")
LOCAL_LINK_RE = re.compile(r"(!?\[[^\]]*\]\(([^)]+)\))")
SECRET_PATTERNS = [
    "sk-" + r"[A-Za-z0-9]{20,}",
    "ghp_" + r"[A-Za-z0-9_]{20,}",
    "xox" + r"[baprs]-",
    r"(?:token|api[_-]?key|secret)\s*=\s*['\"][A-Za-z0-9_\-]{20,}",
]
SECRET_RE = re.compile("(" + "|".join(SECRET_PATTERNS) + ")", re.IGNORECASE)
LOCAL_ONLY_NAME_RE = re.compile(r"(\.env|token|secret|credential|cookie|\.pem|\.p12|id_rsa)", re.IGNORECASE)
# 仅用于识别已完成的历史迁移；正式资产不再依赖顶层集中素材库。
MIGRATION_LEDGER = ROOT / "07-资料与流程/04-索引与报告/文章包迁移记录.md"
HISTORY_ASSET_ARCHIVE = ROOT / "07-资料与流程/03-资产与核验/历史素材归档"
ARCHIVED_INLINE_DIR = HISTORY_ASSET_ARCHIVE / "未入库或下架素材" / "图片" / "归档" / "正文插图-历史未引用"
ARCHIVE_MANIFEST = ROOT / "07-资料与流程/03-资产与核验/图片归档清单.md"
OFFLINE_RELATION = ROOT / "07-资料与流程/02-选题与发布/下架文章与替代关系.md"


def run(cmd: list[str], title: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"\n=== {title} ===")
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, env=env)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    if check and result.returncode != 0:
        raise SystemExit(f"{title} 失败，退出码 {result.returncode}")
    return result


def run_python(script_name: str, title: str, *arguments: str) -> None:
    script = SCRIPTS / "01-发布校验" / script_name
    if not script.is_file():
        raise FileNotFoundError(f"检查脚本不存在：{script.relative_to(ROOT)}")
    run([sys.executable, str(script), *arguments], title)


def parse_asset_records() -> list[dict[str, str]]:
    asset = ROOT / "07-资料与流程" / "03-资产与核验" / "文章资产登记表.md"
    records: list[dict[str, str]] = []
    for line in asset.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line or "编号" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 9 or not cells[0].isdigit():
            continue
        path_cell = cells[5]
        path_match = re.search(r"`([^`]+)`", path_cell)
        records.append({
            "id": cells[0].zfill(2),
            "title": cells[1],
            "path": path_match.group(1) if path_match else path_cell,
            "storage_status": cells[7],
            "repeat_rate": cells[8],
        })
    return records


def read_retired_formal_ids() -> list[str]:
    """Read IDs explicitly marked permanently reserved in the offboarding register."""
    if not OFFLINE_RELATION.exists():
        return []
    ids = {
        match.group(1).zfill(2)
        for line in OFFLINE_RELATION.read_text(encoding="utf-8").splitlines()
        for match in re.finditer(r"\u6c38\u4e45\u4fdd\u7559\u7f16\u53f7[\uff1a:]\s*(\d{1,2})", line)
    }
    return sorted(ids, key=int)


def iter_article_files() -> list[Path]:
    files: list[Path] = []
    for directory in sorted(p for p in ROOT.iterdir() if p.is_dir() and ARTICLE_DIR_RE.match(p.name)):
        for file in sorted(directory.rglob("*.md")):
            if ARTICLE_FILE_RE.match(file.name):
                files.append(file)
    return files


def parse_article_path(path: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"0[1-6]-.+/(?:\d{2}-.+/)?(\d{2})-(.+)\.md", path.replace("\\", "/"))
    if not match:
        return None
    return match.group(1), match.group(2)


def readme_article_rows(readme: Path, article_table_only: bool = False) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    row_re = re.compile(r"^\|\s*(\d{2})\s*\|\s*\[([^\]]+)\]\(<([^>]+)>\)")
    in_article_table = not article_table_only
    for line_no, line in enumerate(readme.read_text(encoding="utf-8").splitlines(), 1):
        if article_table_only and line.startswith("## "):
            in_article_table = line == "## 全部文章"
            continue
        if not in_article_table:
            continue
        match = row_re.match(line)
        if not match:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        repeat_rate = cells[5] if article_table_only and len(cells) >= 7 else ""
        target = (readme.parent / match.group(3)).resolve()
        try:
            relative_target = target.relative_to(ROOT).as_posix()
        except ValueError:
            relative_target = match.group(3)
        rows.append({
            "line": str(line_no),
            "id": match.group(1),
            "title": match.group(2),
            "path": relative_target,
            "repeat_rate": repeat_rate,
        })
    return rows


def check_article_consistency() -> None:
    print("\n=== 正式文章编号、标题与 README 一致性检查 ===")
    records = parse_asset_records()
    files = iter_article_files()
    file_paths = {file.relative_to(ROOT).as_posix() for file in files}
    record_paths = {record["path"] for record in records}
    issues: list[str] = []

    file_ids = sorted((parse_article_path(path)[0] for path in file_paths if parse_article_path(path)), key=int)
    record_ids = [record["id"] for record in records]
    retired_ids = read_retired_formal_ids()
    max_id = max((int(item) for item in [*file_ids, *record_ids]), default=0)
    expected_ids = [
        f"{index:02d}"
        for index in range(1, max_id + 1)
        if f"{index:02d}" not in retired_ids
    ]
    if file_ids != expected_ids:
        issues.append("[P0] Formal article file IDs are not continuous after excluding registered retired IDs")
    if record_ids != expected_ids:
        issues.append("[P0] Asset register IDs are not continuous after excluding registered retired IDs")
    for retired_id in retired_ids:
        if retired_id in file_ids or retired_id in record_ids:
            issues.append(f"[P0] Retired formal ID is still occupied: {retired_id}")

    repeat_rate_pattern = re.compile(r"^\d{1,3}\.\d{2}%$")
    for record in records:
        repeat_rate = record["repeat_rate"]
        if not repeat_rate_pattern.fullmatch(repeat_rate) or float(repeat_rate[:-1]) > 100:
            issues.append(f'[P1] 资产登记表重复率未按两位小数标准记录：{record["id"]} {repeat_rate!r}')
        parsed = parse_article_path(record["path"])
        if parsed is None:
            issues.append(f"[P0] 资产登记表路径不符合文章命名规则：{record['path']}")
            continue
        file_id, file_title = parsed
        if record["id"] != file_id:
            issues.append(
                f"[P0] 资产登记表编号与文件名前缀不一致：登记 {record['id']}，文件 {file_id}，{record['path']}"
            )
        if record["title"] != file_title:
            issues.append(
                f"[P0] 资产登记表标题与文件名标题不一致：登记《{record['title']}》，文件《{file_title}》"
            )

    missing = sorted(record_paths - file_paths)
    extra = sorted(file_paths - record_paths)
    for article_path in missing:
        issues.append(f"[P0] 资产登记表有记录但正文不存在：{article_path}")
    for article_path in extra:
        issues.append(f"[P0] 正文文件存在但未登记资产表：{article_path}")

    root_readme = ROOT / "README.md"
    root_rows = readme_article_rows(root_readme, article_table_only=True)
    expected_rows = [(record["id"], record["title"], record["path"], record["repeat_rate"]) for record in records]
    actual_rows = [(row["id"], row["title"], row["path"], row["repeat_rate"]) for row in root_rows]
    if actual_rows != expected_rows:
        issues.append("[P1] 根 README 的文章编号、标题、链接或重复率与资产登记表不一致")

    readmes = [root_readme]
    readmes.extend(directory / "README.md" for directory in ROOT.iterdir() if directory.is_dir() and ARTICLE_DIR_RE.match(directory.name))
    for readme in readmes:
        rows = readme_article_rows(readme, article_table_only=(readme == root_readme))
        for row in rows:
            parsed = parse_article_path(row["path"])
            if parsed is None:
                issues.append(f"[P0] {readme.relative_to(ROOT)}:{row['line']} 的文章链接无效：{row['path']}")
                continue
            file_id, file_title = parsed
            if row["id"] != file_id:
                issues.append(
                    f"[P0] {readme.relative_to(ROOT)}:{row['line']} 的序号 {row['id']} 与文章文件名前缀 {file_id} 不一致"
                )
            if row["title"] != file_title:
                issues.append(
                    f"[P0] {readme.relative_to(ROOT)}:{row['line']} 的标题《{row['title']}》与文章文件名《{file_title}》不一致"
                )

    print({
        "articleFileCount": len(files),
        "assetCount": len(records),
        "rootReadmeCount": len(root_rows),
        "readmeFilesChecked": len(readmes),
    })
    if issues:
        print("\n".join(issues))
        raise SystemExit("正式文章编号、标题与 README 一致性检查失败")
    print("通过")

def normalize_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        title_match = re.match(r"([^\s]+)\s+[\"'].*[\"']$", target)
        if title_match:
            target = title_match.group(1)
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def check_markdown_links() -> None:
    print("\n=== Markdown 本地链接与图片引用检查 ===")
    missing: list[tuple[str, str]] = []
    checked = 0
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts or ".tmp" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in LOCAL_LINK_RE.finditer(text):
            target = normalize_target(match.group(2))
            if not target or target.startswith("#"):
                continue
            low = target.lower()
            if re.match(r"^[a-z][a-z0-9+.-]*:", low) or low.startswith("//"):
                continue
            absolute = (path.parent / target.replace("/", "\\")).resolve()
            checked += 1
            if not absolute.exists():
                missing.append((str(path.relative_to(ROOT)), target))
    print({"checkedLocalLinks": checked, "missingCount": len(missing)})
    for source, target in missing[:80]:
        print(f"[P0] {source} -> {target}")
    if missing:
        raise SystemExit("Markdown 本地链接与图片引用检查失败")


def approved_registered_offline_deletions(raw: str) -> tuple[list[str], list[str]]:
    """Allow deletions whose active number/title pair is registered as offboarded."""
    approved: list[str] = []
    rejected: list[str] = []
    stems: set[str] = set()
    approved_active_names: set[str] = set()
    approved_duplicate_report_names: set[str] = set()
    if OFFLINE_RELATION.exists():
        released_id_re = re.compile(r"\u5df2\u91ca\u653e\u6b63\u5f0f\u7f16\u53f7[\uff1a:]\s*(\d{1,2})")
        active_purge_re = re.compile(r"\u5df2\u6279\u51c6\u5220\u9664\u73b0\u7528\u6587\u4ef6[\uff1a:]\s*([^|；]+)")
        duplicate_report_purge_re = re.compile(r"\u5df2\u6279\u51c6\u5220\u9664\u67e5\u91cd\u62a5\u544a\u6587\u4ef6[\uff1a:]\s*(.+?\.(?:json|md))\s*(?=；|\||$)")
        for line in OFFLINE_RELATION.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or "\u5df2\u4e0b\u67b6" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3 or not cells[0].isdigit():
                continue
            title = cells[1]
            stems.add(f"{cells[0].zfill(2)}-{title}")
            for match in released_id_re.finditer(line):
                stems.add(f"{match.group(1).zfill(2)}-{title}")
            active_match = active_purge_re.search(line)
            if active_match:
                for item in active_match.group(1).split("\u3001"):
                    name = item.strip().strip("` .")
                    if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".txt")):
                        approved_active_names.add(name)
            for report_match in duplicate_report_purge_re.finditer(line):
                name = report_match.group(1).strip().strip("` .")
                if name.lower().endswith((".json", ".md")):
                    approved_duplicate_report_names.add(name)
    allowed_dirs = {
        "08-\u7d20\u6750\u5e93/\u56fe\u7247/\u6587\u7ae0\u5c01\u9762",
        "08-\u7d20\u6750\u5e93/\u56fe\u7247/\u6b63\u6587\u63d2\u56fe",
        "08-\u7d20\u6750\u5e93/\u56fe\u7247/\u5c01\u9762\u5e95\u56fe",
    }
    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0].startswith("D"):
            rejected.append(line)
            continue
        source = Path(parts[-1].replace("/", "\\"))
        rel_parent = source.parent.as_posix()
        exact = source.stem
        is_formal_article = bool(re.match(r"^0[1-6]-", rel_parent)) and source.suffix.lower() == ".md"
        is_formal_asset = rel_parent in allowed_dirs
        is_article_metadata = rel_parent == "07-资料与流程/03-资产与核验/文章元数据" and source.suffix.lower() == ".json"
        is_duplicate_report = rel_parent == "07-资料与流程/04-索引与报告/内容去重报告" and source.name in approved_duplicate_report_names
        matches_registered_stem = any(exact == stem or exact.startswith(stem + "-") or exact.startswith(stem) for stem in stems)
        matches_explicit_active_file = is_formal_asset and source.name in approved_active_names
        if is_duplicate_report or ((is_formal_article or is_formal_asset or is_article_metadata) and (matches_registered_stem or matches_explicit_active_file)):
            approved.append(line)
        else:
            rejected.append(line)
    return approved, rejected


def approved_archive_deletions(raw: str) -> tuple[list[str], list[str]]:
    """Allow registered moves into the archive and explicitly approved image purges."""
    approved: list[str] = []
    unexpected: list[str] = []
    manifest_text = ARCHIVE_MANIFEST.read_text(encoding="utf-8") if ARCHIVE_MANIFEST.exists() else ""
    approved_purge_names: set[str] = set()
    approved_official_screenshot_names: set[str] = set()
    if OFFLINE_RELATION.exists():
        purge_re = re.compile(r"\u5df2\u6279\u51c6\u5220\u9664\u5f52\u6863\u6587\u4ef6[\uff1a:]\s*([^|；]+)")
        official_purge_re = re.compile(r"\u5df2\u6279\u51c6\u5220\u9664\u5b98\u65b9\u5de5\u5177\u622a\u56fe\u6587\u4ef6[\uff1a:]\s*([^|\uff1b]+)")
        for line in OFFLINE_RELATION.read_text(encoding="utf-8").splitlines():
            for match in purge_re.finditer(line):
                name = match.group(1).strip().strip("` .")
                if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    approved_purge_names.add(name)
            for match in official_purge_re.finditer(line):
                for item in match.group(1).split("、"):
                    name = item.strip().strip("` .")
                    if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                        approved_official_screenshot_names.add(name)

    archive_dir = ARCHIVED_INLINE_DIR.relative_to(ROOT).as_posix()
    official_screenshot_dir = (ROOT / "08-素材库" / "图片" / "官方工具截图").relative_to(ROOT).as_posix()
    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0].startswith("D"):
            unexpected.append(line)
            continue
        source = parts[-1].replace("/", "\\")
        source_path = Path(source)
        target = ARCHIVED_INLINE_DIR / source_path.name
        is_registered_move = (
            source_path.parent.as_posix() == "08-\u7d20\u6750\u5e93/\u56fe\u7247/\u6b63\u6587\u63d2\u56fe"
            and target.exists()
            and source_path.name in manifest_text
        )
        is_approved_purge = (
            source_path.parent.as_posix().startswith("08-素材库/图片/归档/")
            and source_path.name in approved_purge_names
        )
        is_approved_official_screenshot_purge = (
            source_path.parent.as_posix() == official_screenshot_dir
            and source_path.name in approved_official_screenshot_names
        )
        if is_registered_move or is_approved_purge or is_approved_official_screenshot_purge:
            approved.append(line)
        else:
            unexpected.append(line)

    return approved, unexpected


def approved_same_number_replacements(raw: str) -> tuple[list[str], list[str]]:
    """Allow a retitle or complete reindex when its article-title suffix remains in the worktree.

    This keeps the deletion guard strict for real removals, but accepts an explicitly related
    filename migration even when an updated raster asset is emitted as delete/add instead of a Git rename.
    """
    approved: list[str] = []
    rejected: list[str] = []
    asset_paths = [record["path"] for record in parse_asset_records()]
    registered_by_id: dict[str, str] = {}
    for item in asset_paths:
        match = re.match(r"^0[1-6]-[^/]+/(?:\d{2}-[^/]+/)?(\d{2})-", item)
        if match:
            registered_by_id[match.group(1)] = item.replace("/", "\\")

    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        status = parts[0] if parts else ""
        if status.startswith("R"):
            if len(parts) >= 3:
                old_name = Path(parts[1].replace("/", "\\")).name
                new_path = Path(parts[2].replace("/", "\\"))
                old_match = re.match(r"^(\d{2})-", old_name)
                new_match = re.match(r"^(\d{2})-", new_path.name)
                # A complete reindex preserves the title suffix while changing its numeric prefix.
                if old_match and new_match and old_name[3:] == new_path.name[3:] and (ROOT / new_path).exists():
                    approved.append(line)
                    continue
                # Content-deduplication reports are regenerated with a new timestamp during article renumbering.
                old_path = Path(parts[1].replace("/", "\\"))
                report_dir = "07-资料与流程/04-索引与报告/内容去重报告"
                timestamped_report_re = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-(.+\.(?:json|md))$")
                old_report_match = timestamped_report_re.match(old_name)
                new_report_match = timestamped_report_re.match(new_path.name)
                if (
                    old_path.parent.as_posix() == report_dir
                    and new_path.parent.as_posix() == report_dir
                    and old_report_match
                    and new_report_match
                    and old_report_match.group(1) == new_report_match.group(1)
                    and (ROOT / new_path).exists()
                ):
                    approved.append(line)
                    continue
                # Full reindexing preserves the title suffix while replacing its numeric prefix.
                if old_match and new_match and old_name[3:] == new_path.name[3:] and (ROOT / new_path).exists():
                    approved.append(line)
                    continue
                if old_match and new_match and old_match.group(1) == new_match.group(1) and (ROOT / new_path).exists():
                    approved.append(line)
                    continue
                # A regenerated official screenshot may pair a different figure suffix during a reindex;
                # approve only when both paths are inline images for the same article title.
                old_path = Path(parts[1].replace("/", "\\"))
                inline_dir = "08-素材库/图片/正文插图"
                old_title = old_name[3:].split("-正文插图", 1)[0] if old_match else ""
                new_title = new_path.name[3:].split("-正文插图", 1)[0] if new_match else ""
                if (
                    old_match
                    and new_match
                    and old_path.parent.as_posix() == inline_dir
                    and new_path.parent.as_posix() == inline_dir
                    and old_title
                    and old_title == new_title
                    and (ROOT / new_path).exists()
                ):
                    approved.append(line)
                    continue
            rejected.append(line)
            continue
        if len(parts) < 2 or not status.startswith("D"):
            rejected.append(line)
            continue
        source = parts[-1].replace("/", "\\")
        source_path = Path(source)
        match = re.match(r"^(\d{2})-", source_path.name)
        if not match:
            rejected.append(line)
            continue
        no = match.group(1)
        registered = registered_by_id.get(no, "")

        # Article retitle: old formal article path is deleted, but the same id now points to a new file.
        if source_path.parts and re.match(r"^0[1-6]-", source_path.parts[0]) and source_path.suffix.lower() == ".md":
            if registered and registered != source and (ROOT / registered).exists():
                approved.append(line)
                continue

        # Article-package migration: an article-bound legacy image may move beside the body.
        parent = source_path.parent.as_posix()
        if parent in {"08-素材库/图片/文章封面", "08-素材库/图片/正文插图"} and registered:
            package_assets = (ROOT / registered).parent / "assets"
            replacement = package_assets / ("cover" if parent.endswith("文章封面") else "figures") / source_path.name
            if replacement.is_file():
                approved.append(line)
                continue

        # Image retitle/redraw: old same-number image leaves active asset dirs, new same-number image exists.
        if parent in {"08-素材库/图片/文章封面", "08-素材库/图片/正文插图"}:
            suffix_match = re.search(r"(-封面|-正文插图\d+)\.(png|jpe?g|webp)$", source_path.name, re.I)
            if suffix_match:
                suffix = suffix_match.group(0)
                replacement_dir = ROOT / source_path.parent
                replacement_exists = any(
                    q.is_file()
                    and q.name.startswith(no + "-")
                    and q.name != source_path.name
                    and q.name.endswith(suffix)
                    for q in replacement_dir.glob(no + "-*" + suffix)
                )
                if replacement_exists:
                    approved.append(line)
                    continue

        # Complete reindex with a regenerated image: the numeric prefix changes but the title
        # suffix remains. Git may report this as D/A because the image bytes changed, so infer
        # the replacement from its deterministic filename rather than similarity detection.
        parent_dir = ROOT / source_path.parent
        if source_path.parts and source_path.parts[0].startswith("08-") and parent_dir.exists():
            replacement_exists = any(
                candidate.is_file()
                and re.match(r"^\d{2}-", candidate.name)
                and candidate.name[3:] == source_path.name[3:]
                for candidate in parent_dir.iterdir()
            )
            if replacement_exists:
                approved.append(line)
                continue
        rejected.append(line)
    return approved, rejected

def approved_legacy_script_template_archives(raw: str) -> tuple[list[str], list[str]]:
    """Allow approved legacy script/template moves into the historical docs area."""
    approved: list[str] = []
    rejected: list[str] = []
    allowed_names = {
        "reindex_formal_articles.py",
        "封面提示词模板-V1.md",
        "封面提示词模板-V1.2.md",
    }
    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        status = parts[0] if parts else ""
        if not status.startswith("R") or len(parts) < 3:
            rejected.append(line)
            continue
        old_path = Path(parts[1].replace("/", "\\"))
        new_path = Path(parts[2].replace("/", "\\"))
        if (
            old_path.parent.as_posix() == "09-工具脚本"
            and new_path.parent.as_posix() == "07-资料与流程/90-历史记录/历史脚本与模板"
            and old_path.name == new_path.name
            and old_path.name in allowed_names
            and (ROOT / new_path).exists()
        ):
            approved.append(line)
        else:
            rejected.append(line)
    return approved, rejected

def approved_material_library_migration_deletions(raw: str) -> tuple[list[str], list[str]]:
    """仅允许已登记且有保留副本的集中素材库迁移删除。"""
    approved: list[str] = []
    rejected: list[str] = []
    ledger_ok = (
        MIGRATION_LEDGER.is_file()
        and "顶层 `08-素材库/` 已停用并移除" in MIGRATION_LEDGER.read_text(encoding="utf-8")
        and not (ROOT / "08-素材库").exists()
    )
    retained_names = {
        path.name
        for base in [HISTORY_ASSET_ARCHIVE, *ROOT.glob("0[1-6]-*/**/assets")]
        if base.exists()
        for path in base.rglob("*")
        if path.is_file()
    }
    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        status = parts[0] if parts else ""
        if status.startswith("D") and len(parts) >= 2:
            source = parts[-1].replace("\\", "/")
        elif status.startswith("R") and len(parts) >= 3:
            source = parts[1].replace("\\", "/")
        else:
            rejected.append(line)
            continue
        if source.startswith("08-素材库/") and ledger_ok and Path(source).name in retained_names:
            approved.append(line)
        else:
            rejected.append(line)
    return approved, rejected

def approved_article_skill_duplicate_deletions(raw: str) -> tuple[list[str], list[str]]:
    """Allow removal of project-local copies now owned by canonical article-Skill."""
    approved: list[str] = []
    rejected: list[str] = []
    allowed_files = {
        "09-\u5de5\u5177\u811a\u672c/article-wechat-SKILL.md",
        "09-\u5de5\u5177\u811a\u672c/\u5c01\u9762\u63d0\u793a\u8bcd\u6a21\u677f-V1.3.md",
        "09-\u5de5\u5177\u811a\u672c/\u6279\u91cf\u8865\u5168\u6587\u7ae0\u5c01\u9762.py",
        "09-\u5de5\u5177\u811a\u672c/gpt_image_cover.py",
        "09-\u5de5\u5177\u811a\u672c/\u6279\u91cf\u751f\u6210\u914d\u56fe.py",
        # Redundant project adapter note; canonical integration docs remain in the other runbook.
        "09-\u5de5\u5177\u811a\u672c/\u5c01\u9762\u751f\u4ea7\u63a5\u5165\u8bf4\u660e.md",
    }
    allowed_prefixes = ("09-\u5de5\u5177\u811a\u672c/article-wechat-skill/",)
    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        status = parts[0] if parts else ""
        if not status.startswith("D") or len(parts) < 2:
            rejected.append(line)
            continue
        deleted = parts[1].replace("\\", "/")
        if deleted in allowed_files or deleted.startswith(allowed_prefixes):
            approved.append(line)
        else:
            rejected.append(line)
    return approved, rejected


def approved_workflow_reorganization_deletions(raw: str) -> tuple[list[str], list[str]]:
    """Allow only the documented 07/09 directory reorganization and its four retired records."""
    approved: list[str] = []
    rejected: list[str] = []
    docs_root = ROOT / "07-资料与流程"
    tools_root = ROOT / "09-工具脚本"
    reorganization_ok = (
        (docs_root / "README.md").is_file()
        and (tools_root / "README.md").is_file()
        and "01-当前流程" in (docs_root / "README.md").read_text(encoding="utf-8")
        and "01-发布校验" in (tools_root / "README.md").read_text(encoding="utf-8")
    )
    doc_routes = {
        "下架文章与替代关系.md": "02-选题与发布",
        "内容维护清单.md": "01-当前流程",
        "发布记录.md": "02-选题与发布",
        "后续文章生成方案.md": "01-当前流程",
        "后续选题大纲与状态跟踪.md": "90-历史记录",
        "图片归档清单.md": "03-资产与核验",
        "图片生成记录.md": "03-资产与核验",
        "已发布文章去重登记.md": "02-选题与发布",
        "文章包结构说明.md": "01-当前流程",
        "文章质量检查与微信发布规范.md": "01-当前流程",
        "文章资产登记表.md": "03-资产与核验",
        "文章资料核验台账.md": "03-资产与核验",
        "更新工作流.md": "01-当前流程",
        "编号变更记录.md": "02-选题与发布",
        "选题库.md": "02-选题与发布",
        "选题文章绑定表.md": "04-索引与报告",
        "项目结构与文件归位说明.md": "01-当前流程",
        "内容库索引.jsonl": "04-索引与报告",
    }
    retired_docs = {
        "全库文章质量复扫报告-2026-07-17.md",
        "文章发布状态与完整性复查-2026-07-20.md",
        "文章质量分级表.md",
        "选题同步与规划管控机制.md",
    }
    tool_routes = {
        "一键发布检查.py": "01-发布校验",
        "图片视觉检查.py": "01-发布校验",
        "图片资产检查.py": "01-发布校验",
        "文章统一检查.py": "01-发布校验",
        "文章质量扫描.py": "01-发布校验",
        "资料核验检查.py": "01-发布校验",
        "选题文章绑定检查.py": "01-发布校验",
        "重建知识库索引.py": "01-发布校验",
        "内容去重工具.mjs": "02-内容去重与归档",
        "归档外部原文.mjs": "02-内容去重与归档",
        "批量归档微信公众号原创.mjs": "02-内容去重与归档",
        "更新文章资产重复度.mjs": "02-内容去重与归档",
        "检查内容重复度.mjs": "02-内容去重与归档",
        "重建内容库索引.mjs": "02-内容去重与归档",
        "article-skill-project.json": "03-技能接入",
        "article-skill.lock.json": "03-技能接入",
        "article-wechat-skill-说明.md": "03-技能接入",
    }
    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        status = parts[0] if parts else ""
        if not status.startswith("D") or len(parts) < 2 or not reorganization_ok:
            rejected.append(line)
            continue
        source = parts[-1].replace("\\", "/")
        source_path = Path(source)
        replacement: Path | None = None
        if source.startswith("07-资料与流程/内容去重报告/"):
            replacement = docs_root / "04-索引与报告/内容去重报告" / source_path.name
        elif source.startswith("07-资料与流程/文章元数据/"):
            replacement = docs_root / "03-资产与核验/文章元数据" / source_path.name
        elif source.startswith("07-资料与流程/选题草稿/"):
            replacement = docs_root / "02-选题与发布/选题草稿" / source_path.name
        elif source.startswith("07-资料与流程/历史脚本与模板/"):
            replacement = docs_root / "90-历史记录/历史脚本与模板" / source_path.name
        elif source.startswith("07-资料与流程/") and source_path.name in doc_routes:
            replacement = docs_root / doc_routes[source_path.name] / source_path.name
        elif source.startswith("07-资料与流程/") and source_path.name in retired_docs:
            approved.append(line)
            continue
        elif source.startswith("09-工具脚本/") and source_path.name in tool_routes:
            replacement = tools_root / tool_routes[source_path.name] / source_path.name
        if replacement is not None and replacement.is_file():
            approved.append(line)
        else:
            rejected.append(line)
    return approved, rejected


def check_git_deletions() -> None:
    print("\n=== Git 删除检查 ===")
    staged = capture_stdout(["git", "diff", "--cached", "--find-renames=5%", "--name-status", "--diff-filter=DR"]).strip()
    unstaged = capture_stdout(["git", "diff", "--find-renames=5%", "--name-status", "--diff-filter=DR"]).strip()

    approved: list[str] = []
    unexpected: list[str] = []
    for raw in (staged, unstaged):
        accepted_offline, rejected_offline = approved_registered_offline_deletions(raw)
        approved.extend(accepted_offline)
        accepted_replacements, rejected_replacements = approved_same_number_replacements("\n".join(rejected_offline))
        approved.extend(accepted_replacements)
        accepted_archives, rejected_archives = approved_archive_deletions("\n".join(rejected_replacements))
        approved.extend(accepted_archives)
        accepted_library_migrations, rejected_library_migrations = approved_material_library_migration_deletions("\n".join(rejected_archives))
        approved.extend(accepted_library_migrations)
        accepted_legacy_archives, rejected_legacy_archives = approved_legacy_script_template_archives("\n".join(rejected_library_migrations))
        approved.extend(accepted_legacy_archives)
        accepted_duplicate_deletions, rejected_duplicate_deletions = approved_article_skill_duplicate_deletions("\n".join(rejected_legacy_archives))
        approved.extend(accepted_duplicate_deletions)
        accepted_reorganization, rejected_reorganization = approved_workflow_reorganization_deletions("\n".join(rejected_duplicate_deletions))
        approved.extend(accepted_reorganization)
        unexpected.extend(rejected_reorganization)

    if approved:
        print(f"已识别 {len(approved)} 项已登记的归档迁移、同编号重命名或 article-Skill 重复代码删除。")
    if unexpected:
        print("\n".join(unexpected))
        raise SystemExit("存在未登记的删除项，请确认是否为预期删除")
    print("通过")

def capture(cmd: list[str]) -> str:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, env=env)
    return (result.stdout or "") + (result.stderr or "")


def capture_stdout(cmd: list[str]) -> str:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, env=env)
    return result.stdout or ""


def added_lines_from_diff(diff_text: str) -> str:
    """Return only newly added diff lines so removed historical code does not create false positives."""
    lines: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++") or not line.startswith("+"):
            continue
        lines.append(line[1:])
    return "\n".join(lines)

def check_secret_risk() -> None:
    print("\n=== 敏感信息检查 ===")
    status = capture(["git", "status", "--porcelain=v1"])
    risky_names = [line for line in status.splitlines() if LOCAL_ONLY_NAME_RE.search(line)]
    if risky_names:
        for line in risky_names:
            print(f"[P0] 文件名疑似本地敏感文件：{line}")
        raise SystemExit("文件名敏感信息检查失败")

    diff = capture(["git", "diff", "--", ":!*.png", ":!*.jpg", ":!*.jpeg", ":!*.webp", ":!*.gif"])
    cached_diff = capture(["git", "diff", "--cached", "--", ":!*.png", ":!*.jpg", ":!*.jpeg", ":!*.webp", ":!*.gif"])
    scan_text = "\n".join([added_lines_from_diff(diff), added_lines_from_diff(cached_diff)])
    if SECRET_RE.search(scan_text):
        raise SystemExit("发现新增疑似密钥或 Token，请先人工排查")
    print("通过")


def main() -> int:
    print("一键发布前检查开始：检查并重建索引，不提交、不推送。")
    run_python("重建知识库索引.py", "重建知识库索引")
    run_python("资料核验检查.py", "资料核验检查与台账重建", "--write-ledger")
    run_python("文章质量扫描.py", "文章质量扫描")
    run_python("选题文章绑定检查.py", "选题文章绑定检查")
    run_python("图片资产检查.py", "图片资产检查")
    run_python("图片视觉检查.py", "图片视觉检查")
    check_markdown_links()
    check_article_consistency()
    run(["git", "diff", "--check"], "Git 格式检查")
    check_git_deletions()
    check_secret_risk()
    print("\n全部检查通过。可以按需提交并推送 main。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
