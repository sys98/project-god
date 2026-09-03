#!/usr/bin/env python3
"""Safely copy project-template governance files into a new or existing project."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote, urlparse


PLACEHOLDER = re.compile(r"__[A-Z0-9_]+__")
FORGE_PROJECT = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+$")
GITLAB_ONLY_FILES = (
    Path(".gitlab-ci.yml"),
    Path("docs/agents/gitlab-api-operations.md"),
    Path("tools/gitlab-api.sh"),
    Path("tools/gitlab-api.test.sh"),
)


class ScaffoldError(Exception):
    pass


def default_template_root() -> Path:
    """Root containing template/: nearest ancestor with template/AGENTS.md.

    Repo layout resolves to the repository root; a copied skill install
    (install.sh --copy) carries template/ inside the skill directory.
    """
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "template" / "AGENTS.md").is_file():
            return ancestor
    return here.parents[4]


def parse_args() -> argparse.Namespace:
    default_root = default_template_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--forge", required=True, choices=("github", "gitlab", "none"))
    parser.add_argument("--forge-project")
    parser.add_argument("--forge-url")
    parser.add_argument("--mode", choices=("new", "integrate"), default="new")
    parser.add_argument("--template-root", type=Path, default=default_root)
    return parser.parse_args()


def validate(args: argparse.Namespace) -> tuple[Path, Path]:
    template_root = args.template_root.expanduser().resolve()
    source = template_root / "template"
    destination_input = args.destination.expanduser()
    if not destination_input.is_absolute():
        raise ScaffoldError("destination must be an absolute path")
    destination = destination_input.resolve()

    if not source.is_dir():
        raise ScaffoldError(f"template directory not found: {source}")
    if destination == Path("/") or destination == Path.home().resolve():
        raise ScaffoldError(f"refusing broad destination: {destination}")
    if destination == template_root or template_root in destination.parents:
        raise ScaffoldError("destination must be outside the project-template repository")
    if not args.name.strip() or any(character in args.name for character in ("/", "\\", "\r", "\n", "\0")):
        raise ScaffoldError("name must be non-empty and contain no path separators or control characters")
    if args.forge in ("github", "gitlab") and not args.forge_project:
        raise ScaffoldError(f"--forge-project is required for {args.forge}")
    if args.forge_project and not FORGE_PROJECT.fullmatch(args.forge_project):
        raise ScaffoldError("forge project must use owner/project or group/subgroup/project form")
    if args.forge == "gitlab" and not args.forge_url:
        raise ScaffoldError("--forge-url is required for gitlab")
    if args.forge_url:
        parsed_url = urlparse(args.forge_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ScaffoldError("forge URL must be an absolute HTTPS URL")
    if args.mode == "integrate" and not destination.is_dir():
        raise ScaffoldError("integrate mode requires an existing destination directory")
    if args.mode == "new" and destination.exists():
        if not destination.is_dir():
            raise ScaffoldError("destination exists and is not a directory")
        if any(destination.iterdir()):
            raise ScaffoldError("new mode requires a missing or empty destination")
    return source, destination


def forge_values(args: argparse.Namespace) -> dict[str, str]:
    project = args.forge_project or "未配置远程"
    if args.forge == "github":
        forge_name = "GitHub"
        project_url = args.forge_url or f"https://github.com/{project}"
    elif args.forge == "gitlab":
        forge_name = "GitLab"
        project_url = args.forge_url
    else:
        forge_name = "本地 Git"
        project_url = "未配置远程"

    return {
        "__PROJECT_NAME__": args.name,
        "__FORGE__": forge_name,
        "__FORGE_PROJECT__": project,
        "__FORGE_PROJECT_URL__": project_url,
        "__GITLAB_PROJECT__": project,
        "__GITLAB_PROJECT_ENCODED__": quote(project, safe=""),
    }


def prune_platform_files(stage: Path, forge: str) -> None:
    if forge == "gitlab":
        return
    for relative_path in GITLAB_ONLY_FILES:
        path = stage / relative_path
        if path.exists():
            path.unlink()

    tools = stage / "tools"
    if tools.is_dir():
        meaningful = [
            path
            for path in tools.rglob("*")
            if path.is_file() and path.name not in {"AGENTS.md", "CLAUDE.md"}
        ]
        if not meaningful:
            shutil.rmtree(tools)


def replace_placeholders(stage: Path, replacements: dict[str, str]) -> None:
    for path in stage.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = content
        for placeholder, value in replacements.items():
            updated = updated.replace(placeholder, value)
        if updated != content:
            path.write_text(updated, encoding="utf-8")


def unresolved_placeholders(stage: Path) -> list[str]:
    unresolved: list[str] = []
    for path in stage.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if PLACEHOLDER.search(content):
            unresolved.append(str(path.relative_to(stage)))
    return unresolved


def copy_stage(stage: Path, destination: Path, mode: str) -> None:
    if mode == "integrate":
        collisions = []
        for path in stage.rglob("*"):
            relative_path = path.relative_to(stage)
            target = destination / relative_path
            if path.is_file() and (target.exists() or target.is_symlink()):
                collisions.append(str(relative_path))
            elif path.is_dir() and target.exists() and not target.is_dir():
                collisions.append(str(relative_path))
        collisions.sort()
        if collisions:
            preview = ", ".join(collisions[:5])
            suffix = "..." if len(collisions) > 5 else ""
            raise ScaffoldError(f"integration would overwrite existing files: {preview}{suffix}")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(stage, destination, dirs_exist_ok=True)


def main() -> int:
    args = parse_args()
    try:
        source, destination = validate(args)
        with tempfile.TemporaryDirectory(prefix="project-template-scaffold-") as temporary:
            stage = Path(temporary) / "stage"
            shutil.copytree(source, stage)
            prune_platform_files(stage, args.forge)
            replace_placeholders(stage, forge_values(args))
            unresolved = unresolved_placeholders(stage)
            if unresolved:
                raise ScaffoldError(f"unresolved placeholders: {', '.join(unresolved)}")
            copy_stage(stage, destination, args.mode)
    except (OSError, ScaffoldError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"created: {destination}")
    print(f"mode: {args.mode}  forge: {args.forge}  project: {args.forge_project or 'none'}")
    print("next: close AGENTS.md <initialization> with the confirmed project contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
