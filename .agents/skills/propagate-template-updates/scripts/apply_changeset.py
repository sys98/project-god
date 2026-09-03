#!/usr/bin/env python3
"""Fail-closed application of a template propagation changeset to one derived project.

Changeset JSON: {"units": [...]}, at most one unit per file. Kinds:
  replace: {"file", "kind": "replace", "pairs": [{"old", "new"}, ...]}
           Every old must occur exactly once; all pairs of a file pass or the file stays untouched.
  add:     {"file", "kind": "add", "source": "template/..."}
           Copies a template file in; refuses when the target exists or its parent dir is missing.
  sync:    {"file", "kind": "sync", "source": "template/...", "require_sha256": "<hex>"}
           Overwrites with the template file; refuses unless the current content matches the sha.

Prints the plan for every unit; writes only under --apply.
Exit 0 when every unit applied (or planned), 2 when any unit was refused, 1 on usage or IO errors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

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


REPO_ROOT = default_template_root()
KINDS = ("replace", "add", "sync")


class Refusal(Exception):
    """One unit is unsafe to apply; its file stays untouched."""


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--changeset", required=True, type=Path)
    parser.add_argument("--template-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def resolve_under(root: Path, relative: str) -> Path:
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        die(f"路径越出根目录: {relative}")
    return resolved


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_units(path: Path) -> list[dict]:
    try:
        units = json.loads(path.read_text(encoding="utf-8"))["units"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        die(f"changeset 不可解析: {error}")
    if not isinstance(units, list) or not units:
        die("changeset.units 必须是非空列表")
    seen: set[str] = set()
    for unit in units:
        if not isinstance(unit, dict) or unit.get("kind") not in KINDS or not isinstance(unit.get("file"), str):
            die(f"单元缺 file/kind 或 kind 未知: {str(unit)[:80]}")
        if unit["kind"] == "replace":
            pairs = unit.get("pairs")
            if not isinstance(pairs, list) or not pairs:
                die(f"replace 单元缺 pairs: {unit['file']}")
            for pair in pairs:
                if not isinstance(pair, dict) or not pair.get("old") or not isinstance(pair.get("new"), str):
                    die(f"pair 缺 old/new: {str(pair)[:80]}")
                if pair["old"] == pair["new"]:
                    die(f"pair old==new: {unit['file']}")
        if unit["kind"] in ("add", "sync") and not isinstance(unit.get("source"), str):
            die(f"{unit['kind']} 单元缺 source: {unit['file']}")
        if unit["file"] in seen:
            die(f"同一文件出现多个单元: {unit['file']}")
        seen.add(unit["file"])
    return units


def check_replace(target: Path, pairs: list) -> str:
    if not target.is_file():
        raise Refusal("目标文件不存在")
    text = target.read_text(encoding="utf-8")
    for pair in pairs:
        count = text.count(pair["old"])
        if count != 1:
            raise Refusal(f"锚点出现 {count} 次: {pair['old'][:40]!r}")
    return f"{len(pairs)} 个锚点替换"


def check_add(target: Path, source: Path) -> str:
    if target.exists():
        raise Refusal("目标已存在（add 只处理缺失文件）")
    if not target.parent.is_dir():
        raise Refusal(f"目标父目录不存在: {target.parent}")
    if not source.is_file():
        raise Refusal(f"模板源不存在: {source}")
    return f"新增自 {source.name}"


def check_sync(target: Path, source: Path, required: str) -> str:
    if not target.is_file():
        raise Refusal("目标文件不存在")
    if not source.is_file():
        raise Refusal(f"模板源不存在: {source}")
    current = sha256(target.read_bytes())
    if current != required:
        raise Refusal(f"当前内容 sha256 与已证实版本不符: {current[:12]}…")
    if sha256(source.read_bytes()) == current:
        raise Refusal("内容与模板当前版本一致，无需同步")
    return "整文件 fast-forward"


def plan(project: Path, template_root: Path, unit: dict) -> tuple[Path, dict, str]:
    target = resolve_under(project, unit["file"])
    source = resolve_under(template_root, unit["source"]) if "source" in unit else None
    if unit["kind"] == "replace":
        summary = check_replace(target, unit["pairs"])
    elif unit["kind"] == "add":
        summary = check_add(target, source)
    else:
        summary = check_sync(target, source, unit.get("require_sha256", ""))
    return target, unit, summary


def apply_unit(template_root: Path, target: Path, unit: dict) -> None:
    if unit["kind"] == "replace":
        text = target.read_text(encoding="utf-8")
        for pair in unit["pairs"]:
            text = text.replace(pair["old"], pair["new"], 1)
        target.write_text(text, encoding="utf-8")
    else:
        target.write_bytes(resolve_under(template_root, unit["source"]).read_bytes())


def main() -> int:
    args = parse_args()
    project = args.project.resolve()
    if not (project / "AGENTS.md").is_file():
        die(f"{project} 不含 AGENTS.md，不是可识别的派生项目")
    template_root = args.template_root.resolve()
    units = load_units(args.changeset)

    planned: list[tuple[Path, dict, str]] = []
    refused = 0
    for unit in units:
        try:
            target, planned_unit, summary = plan(project, template_root, unit)
            planned.append((target, planned_unit, summary))
            print(f"  plan   {unit['file']}: {summary}")
        except Refusal as refusal:
            refused += 1
            print(f"  refuse {unit['file']}: {refusal}")

    if not args.apply:
        print("dry-run：加 --apply 才写入")
    else:
        for target, unit, _ in planned:
            apply_unit(template_root, target, unit)
            print(f"  wrote  {unit['file']}")

    if refused:
        print(f"{refused} 个单元被拒（Needs-Decision）")
        return 2
    print(f"ok: {len(planned)} 个单元{'已应用' if args.apply else '通过检查'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
