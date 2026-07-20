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
    continuous = readme_numbers == list(range(1, len(readme_numbers) + 1))

    print({
        "articleFileCount": len(files),
        "assetCount": len(asset_ids),
        "readmeCount": len(readme_rows),
        "readmeContinuous": continuous,
        "assetIds": asset_ids,
    })
    if missing:
        for path in missing:
            print(f"[P0] 资产登记表有记录但正文不存在：{path}")
    if extra:
        for path in extra:
            print(f"[P0] 正文文件存在但未登记资产表：{path}")
    if not continuous:
        print("[P1] README 连续阅读序号不连续")
    if missing or extra or not continuous or not (len(files) == len(asset_ids) == len(readme_rows)):
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


def check_git_deletions() -> None:
    print("\n=== Git 删除检查 ===")
    staged = run(["git", "diff", "--cached", "--name-status", "--diff-filter=D"], "暂存区删除检查", check=False).stdout.strip()
    unstaged = run(["git", "diff", "--name-status", "--diff-filter=D"], "工作区删除检查", check=False).stdout.strip()
    if staged or unstaged:
        print(staged)
        print(unstaged)
        raise SystemExit("存在删除项，请确认是否为预期删除")
    print("通过")


def capture(cmd: list[str]) -> str:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, env=env)
    return (result.stdout or "") + (result.stderr or "")


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
    check_markdown_links()
    check_article_consistency()
    run(["git", "diff", "--check"], "Git 格式检查")
    check_git_deletions()
    check_secret_risk()
    print("\n全部检查通过。可以按需提交并推送 main。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
