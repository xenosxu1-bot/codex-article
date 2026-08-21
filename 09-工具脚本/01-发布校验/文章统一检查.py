#!/usr/bin/env python3
"""Run the canonical article-Skill package validator without a project-side lock file."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the canonical article-Skill package validator")
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


def locate_article(article_id: str) -> Path:
    """Locate a formal article in either the legacy flat layout or an article package."""
    patterns = (
        f"[0-9][0-9]-*/{article_id}-*.md",
        f"[0-9][0-9]-*/{article_id}-*/{article_id}-*.md",
    )
    matches = sorted({path.resolve() for pattern in patterns for path in REPO_ROOT.glob(pattern)})
    if len(matches) != 1:
        detail = "; ".join(patterns)
        raise FileNotFoundError(f"article must resolve to exactly one file; found {len(matches)} for {detail}")
    return matches[0]


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


def verify_skill_worktree(root: Path) -> Path:
    checker = root / "scripts" / "validate_article_package.py"
    if not checker.is_file():
        raise FileNotFoundError("validate_article_package.py is missing")
    if git_output(root, "rev-parse", "--is-inside-work-tree") != "true":
        raise FileNotFoundError("candidate is not a Git worktree")
    if git_output(root, "status", "--porcelain"):
        raise FileNotFoundError("canonical article-Skill worktree has uncommitted changes")
    return root


def locate_skill_root(arg_value: str | None) -> Path:
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
            return verify_skill_worktree(root)
        except FileNotFoundError as error:
            errors.append(f"{root}: {error}")
    details = " | ".join(errors) or "no canonical source path was supplied"
    raise FileNotFoundError(
        "A clean canonical article-Skill Git worktree was not available. "
        "Use --skill-root or ARTICLE_SKILL_ROOT. "
        f"Details: {details}"
    )


def run_validator(checker: Path, article: Path, manifest: Path, tier: str, strict: bool, emit_json: bool) -> int:
    """Invoke the canonical validator with an ephemeral compatibility config.

    The current canonical validator still requires a config path for package
    validation. The project no longer stores or versions a project adapter;
    an empty temporary JSON file satisfies that interface without creating a
    second project-level source of truth.
    """
    temporary_config: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump({}, handle)
            handle.write("\n")
            temporary_config = Path(handle.name)
        command = [
            sys.executable,
            str(checker),
            "--root",
            str(REPO_ROOT),
            "--config",
            str(temporary_config),
            "--article",
            str(article.relative_to(REPO_ROOT)),
            "--manifest",
            str(manifest.relative_to(REPO_ROOT)),
            "--tier",
            tier,
        ]
        if strict:
            command.append("--strict")
        if emit_json:
            command.append("--json")
        return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode
    finally:
        if temporary_config is not None:
            temporary_config.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    if not args.id and not args.article:
        raise ValueError("Provide --id or --article")
    article_id = normalize_id(args.id) if args.id else None
    article = Path(args.article) if args.article else locate_article(article_id)
    if not article.is_absolute():
        article = (REPO_ROOT / article).resolve()
    manifest = Path(args.manifest) if args.manifest else locate_one(f"07-资料与流程/03-资产与核验/文章元数据/{article_id}-*.json", "metadata")
    if not manifest.is_absolute():
        manifest = (REPO_ROOT / manifest).resolve()
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    tier = args.tier or manifest_data.get("article", {}).get("tier", "standard")
    skill_root = locate_skill_root(args.skill_root)
    checker = skill_root / "scripts" / "validate_article_package.py"
    return run_validator(checker, article, manifest, tier, args.strict, args.json)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"Unified check was not run: {error}", file=sys.stderr)
        raise SystemExit(2)
