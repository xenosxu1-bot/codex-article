#!/usr/bin/env python3
"""Run the locked canonical article-Skill package validator by article identifier."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "09-\u5de5\u5177\u811a\u672c"
CONFIG_PATH = TOOLS_ROOT / "article-skill-project.json"
LOCK_PATH = TOOLS_ROOT / "article-skill.lock.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the locked article-Skill package validator")
    parser.add_argument("--id", help="two or more digit article identifier, for example 29")
    parser.add_argument("--article", help="relative article path; omit to locate by identifier")
    parser.add_argument("--manifest", help="relative metadata path; omit to locate by identifier")
    parser.add_argument("--tier", choices=("quick", "standard", "deep"), help="production tier; default comes from metadata")
    parser.add_argument("--skill-root", help="canonical article-Skill Git worktree")
    parser.add_argument("--strict", action="store_true", help="treat P1 suggestions as failures")
    parser.add_argument("--json", action="store_true", help="emit JSON result")
    return parser.parse_args()


def normalize_id(value: str) -> str:
    if not value or not value.isdigit():
        raise ValueError("--id must be numeric")
    return f"{int(value):02d}"


def locate_one(pattern: str, label: str) -> Path:
    matches = sorted(REPO_ROOT.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"{label} must resolve to exactly one file; found {len(matches)} for {pattern}")
    return matches[0]


def load_lock() -> dict[str, str]:
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    canonical = data.get("canonical_skill", {})
    commit = str(canonical.get("commit", "")).strip().lower()
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise ValueError(f"Invalid canonical_skill.commit in {LOCK_PATH.relative_to(REPO_ROOT)}")
    return {"commit": commit, "repository": str(canonical.get("repository", "")), "branch": str(canonical.get("branch", ""))}


def git_output(root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as error:
        raise FileNotFoundError("Git is required to validate the canonical article-Skill worktree") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown Git error"
        raise FileNotFoundError(f"Cannot inspect canonical article-Skill worktree: {detail}")
    return completed.stdout.strip()


def verify_locked_skill(root: Path, lock: dict[str, str]) -> Path:
    checker = root / "scripts" / "validate_article_package.py"
    if not checker.is_file():
        raise FileNotFoundError("validate_article_package.py is missing")
    if git_output(root, "rev-parse", "--is-inside-work-tree") != "true":
        raise FileNotFoundError("candidate is not a Git worktree")
    head = git_output(root, "rev-parse", "HEAD").lower()
    if head != lock["commit"]:
        raise FileNotFoundError(
            f"canonical article-Skill commit mismatch: expected {lock['commit']}, got {head}. "
            "Update the lock only after the source repository is validated and pushed."
        )
    if git_output(root, "status", "--porcelain"):
        raise FileNotFoundError("canonical article-Skill worktree has uncommitted changes")
    return root


def locate_skill_root(arg_value: str | None, lock: dict[str, str]) -> Path:
    candidates = [arg_value, os.getenv("ARTICLE_SKILL_ROOT"), str(REPO_ROOT.parent / "article-Skill")]
    errors: list[str] = []
    seen: set[Path] = set()
    for value in candidates:
        if not value:
            continue
        root = Path(value).expanduser().resolve()
        if root in seen:
            continue
        seen.add(root)
        if not root.exists():
            errors.append(f"{root}: path does not exist")
            continue
        try:
            return verify_locked_skill(root, lock)
        except FileNotFoundError as error:
            errors.append(f"{root}: {error}")
    details = " | ".join(errors) or "no canonical source path was supplied"
    raise FileNotFoundError(
        "Locked canonical article-Skill was not available. Use --skill-root or ARTICLE_SKILL_ROOT with a clean Git worktree matching article-skill.lock.json. "
        f"Details: {details}"
    )


def main() -> int:
    args = parse_args()
    if not args.id and not args.article:
        raise ValueError("Provide --id or --article")
    json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = load_lock()
    article = Path(args.article) if args.article else locate_one(f"[0-9][0-9]-*/{normalize_id(args.id)}-*.md", "article")
    if not article.is_absolute():
        article = (REPO_ROOT / article).resolve()
    manifest = Path(args.manifest) if args.manifest else locate_one(f"07-资料与流程/文章元数据/{normalize_id(args.id)}-*.json", "metadata")
    if not manifest.is_absolute():
        manifest = (REPO_ROOT / manifest).resolve()
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    tier = args.tier or manifest_data.get("article", {}).get("tier", "standard")
    skill_root = locate_skill_root(args.skill_root, lock)
    checker = skill_root / "scripts" / "validate_article_package.py"
    command = [
        sys.executable, str(checker), "--root", str(REPO_ROOT), "--config", str(CONFIG_PATH),
        "--article", str(article.relative_to(REPO_ROOT)), "--manifest", str(manifest.relative_to(REPO_ROOT)), "--tier", tier,
    ]
    if args.strict:
        command.append("--strict")
    if args.json:
        command.append("--json")
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"Unified check was not run: {error}", file=sys.stderr)
        raise SystemExit(2)
