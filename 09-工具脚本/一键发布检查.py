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

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "09-工具脚本"
ARTICLE_DIR_RE = re.compile(r"^0[1-6]-")
ARTICLE_FILE_RE = re.compile(r"^\d{2}-.+\.md$")
LOCAL_LINK_RE = re.compile(r"(!?\[[^\]]*\]\(([^)]+)\))")
SECRET_PATTERNS = [
    "OPENAI" + "_API" + "_KEY",
    "sk-" + r"[A-Za-z0-9]{20,}",
    "ghp_" + r"[A-Za-z0-9_]{20,}",
    "xox" + r"[baprs]-",
    r"token\s*=",
    r"api[_-]?key\s*=",
    r"secret\s*=",
]
SECRET_RE = re.compile("(" + "|".join(SECRET_PATTERNS) + ")", re.IGNORECASE)
LOCAL_ONLY_NAME_RE = re.compile(r"(\.env|token|secret|credential|cookie|\.pem|\.p12|id_rsa)", re.IGNORECASE)
ARCHIVED_INLINE_DIR = ROOT / "08-素材库/图片/归档/正文插图-历史未引用"
ARCHIVE_MANIFEST = ROOT / "07-资料与流程/图片归档清单.md"


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


def run_python(script_name: str, title: str) -> None:
    run([sys.executable, str(SCRIPTS / script_name)], title)


def parse_asset_ids() -> tuple[list[int], list[str]]:
    asset = ROOT / "07-资料与流程" / "文章资产登记表.md"
    ids: list[int] = []
    paths: list[str] = []
    for line in asset.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line or "编号" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].isdigit():
            ids.append(int(cells[0]))
            if len(cells) >= 6:
                match = re.search(r"`([^`]+)`", cells[5])
                paths.append(match.group(1) if match else cells[5])
    return ids, paths


def iter_article_files() -> list[Path]:
    files: list[Path] = []
    for directory in sorted(p for p in ROOT.iterdir() if p.is_dir() and ARTICLE_DIR_RE.match(p.name)):
        for file in sorted(directory.glob("*.md")):
            if ARTICLE_FILE_RE.match(file.name):
                files.append(file)
    return files


def check_article_consistency() -> None:
    print("\n=== 正式文章数量一致性检查 ===")
    asset_ids, asset_paths = parse_asset_ids()
    files = iter_article_files()
    file_paths = {str(p.relative_to(ROOT)).replace("\\", "/") for p in files}
    missing = [p for p in asset_paths if p not in file_paths]
    extra = sorted(file_paths - set(asset_paths))

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_rows = [line for line in readme.splitlines() if re.match(r"^\| \d{2} \|", line)]
    readme_numbers = [int(re.match(r"^\| (\d{2}) \|", line).group(1)) for line in readme_rows]
    readme_matches_asset_ids = readme_numbers == asset_ids

    print({
        "articleFileCount": len(files),
        "assetCount": len(asset_ids),
        "readmeCount": len(readme_rows),
        "readmeMatchesAssetIds": readme_matches_asset_ids,
        "assetIds": asset_ids,
    })
    if missing:
        for path in missing:
            print(f"[P0] 资产登记表有记录但正文不存在：{path}")
    if extra:
        for path in extra:
            print(f"[P0] 正文文件存在但未登记资产表：{path}")
    if not readme_matches_asset_ids:
        print("[P1] README 展示编号与文章文件名前缀或资产登记表不一致")
    if missing or extra or not readme_matches_asset_ids or not (len(files) == len(asset_ids) == len(readme_rows)):
        raise SystemExit("正式文章数量一致性检查失败")
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
        if ".git" in path.parts:
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


def approved_archive_deletions(raw: str) -> tuple[list[str], list[str]]:
    approved: list[str] = []
    unexpected: list[str] = []
    manifest_text = ARCHIVE_MANIFEST.read_text(encoding="utf-8") if ARCHIVE_MANIFEST.exists() else ""

    for line in filter(None, raw.splitlines()):
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0].startswith("D"):
            unexpected.append(line)
            continue
        source = parts[-1].replace("/", "\\")
        source_path = Path(source)
        target = ARCHIVED_INLINE_DIR / source_path.name
        if (
            source_path.parent.as_posix() == "08-素材库/图片/正文插图"
            and target.exists()
            and source_path.name in manifest_text
        ):
            approved.append(line)
        else:
            unexpected.append(line)

    return approved, unexpected



def approved_same_number_replacements(raw: str) -> tuple[list[str], list[str]]:
    """Allow an article/title asset rename when the same numeric id has a new registered path.

    This keeps the deletion guard strict for real removals, but does not block a planned retitle
    where article file and image prefix are replaced under the same article number.
    """
    approved: list[str] = []
    rejected: list[str] = []
    _ids, asset_paths = parse_asset_ids()
    registered_by_id: dict[str, str] = {}
    for item in asset_paths:
        match = re.match(r"^0[1-6]-[^/]+/(\d{2})-", item)
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
                if old_match and new_match and old_match.group(1) == new_match.group(1) and (ROOT / new_path).exists():
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
        if re.match(r"^0[1-6]-", source_path.parent.as_posix()) and source_path.suffix.lower() == ".md":
            if registered and registered != source and (ROOT / registered).exists():
                approved.append(line)
                continue

        # Image retitle/redraw: old same-number image leaves active asset dirs, new same-number image exists.
        parent = source_path.parent.as_posix()
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
        rejected.append(line)
    return approved, rejected

def check_git_deletions() -> None:
    print("\n=== Git 删除检查 ===")
    staged = capture_stdout(["git", "diff", "--cached", "--find-renames=5%", "--name-status", "--diff-filter=DR"]).strip()
    unstaged = capture_stdout(["git", "diff", "--find-renames=5%", "--name-status", "--diff-filter=DR"]).strip()

    approved: list[str] = []
    unexpected: list[str] = []
    for raw in (staged, unstaged):
        accepted_replacements, rejected_replacements = approved_same_number_replacements(raw)
        approved.extend(accepted_replacements)
        accepted_archives, rejected_archives = approved_archive_deletions("\n".join(rejected_replacements))
        approved.extend(accepted_archives)
        unexpected.extend(rejected_archives)

    if approved:
        print(f"已识别 {len(approved)} 项已登记的归档迁移或同编号重命名。")
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
    if SECRET_RE.search(diff) or SECRET_RE.search(cached_diff):
        raise SystemExit("发现疑似密钥或 Token，请先人工排查")
    print("通过")


def main() -> int:
    print("一键发布前检查开始：只检查和重建索引，不提交、不推送。")
    run_python("重建知识库索引.py", "重建知识库索引")
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
