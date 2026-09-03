#!/usr/bin/env python3
"""Validate context pointers in agent-facing docs.

repo:// coordinates and relative Markdown links must resolve to real
files, and "第 N 节" references must point at sections that exist.
Pointers that silently rot are the template's most invisible failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template"

SCAN_FILES = sorted(ROOT.glob("*.md"))
SCAN_DIRS = [TEMPLATE, ROOT / ".agents"]

REPO_RE = re.compile(r"repo://([A-Za-z0-9_./-]+?\.(?:md|sh|yml|yaml|json|py|toml))(?:\s*第\s*(\d+)\s*节)?")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^## ", re.MULTILINE)


def section_count(path: Path) -> int:
    return len(HEADING_RE.findall(path.read_text(encoding="utf-8")))


def main() -> int:
    docs = list(SCAN_FILES)
    for directory in SCAN_DIRS:
        docs.extend(sorted(directory.rglob("*.md")))

    failures: list[str] = []
    for doc in docs:
        if ".git" in doc.parts:
            continue
        label = doc.relative_to(ROOT)
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), start=1):
            for match in REPO_RE.finditer(line):
                target, section = match.groups()
                resolved = TEMPLATE / target
                if not resolved.is_file():
                    failures.append(f"{label}:{lineno}: repo://{target} 不存在")
                elif section and section_count(resolved) < int(section):
                    failures.append(f"{label}:{lineno}: repo://{target} 没有第 {section} 节")
            for match in LINK_RE.finditer(line):
                target = match.group(1).split("#")[0]
                if not target or re.match(r"[a-z][a-z0-9+.-]*:", target):
                    continue
                if not (doc.parent / target).resolve().is_file():
                    failures.append(f"{label}:{lineno}: 链接 {target} 不存在")

    if failures:
        print("context pointer 检查失败：")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"ok: {len(docs)} 个文档中的 context pointer 全部可解析")
    return 0


if __name__ == "__main__":
    sys.exit(main())
