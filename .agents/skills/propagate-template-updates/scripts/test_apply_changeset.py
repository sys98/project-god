#!/usr/bin/env python3
"""Runnable smoke checks for apply_changeset.py."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("apply_changeset.py")


def run(*arguments: str, code: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == code, result.stdout + result.stderr
    return result


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="changeset-test-") as temporary:
        root = Path(temporary)

        template = root / "repo"
        (template / "template/docs/agents").mkdir(parents=True)
        (template / "template/docs/agents/rules.md").write_text("新规则\n", encoding="utf-8")

        project = root / "derived"
        (project / "docs/agents").mkdir(parents=True)
        (project / "AGENTS.md").write_text("# 项目\n旧失败行。\n旧删除行。\n", encoding="utf-8")
        (project / "docs/agents/dup.md").write_text("锚点\n锚点\n", encoding="utf-8")

        def write_changeset(units: list) -> Path:
            path = root / "changeset.json"
            path.write_text(json.dumps({"units": units}, ensure_ascii=False), encoding="utf-8")
            return path

        changeset = write_changeset([
            {"file": "AGENTS.md", "kind": "replace", "pairs": [
                {"old": "旧失败行。", "new": "新失败行。"},
                {"old": "旧删除行。", "new": "新删除行。"},
            ]},
            {"file": "docs/agents/rules.md", "kind": "add", "source": "template/docs/agents/rules.md"},
        ])
        run("--project", str(project), "--changeset", str(changeset), "--template-root", str(template), "--apply")
        text = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "新失败行。" in text and "旧失败行。" not in text
        assert (project / "docs/agents/rules.md").read_text(encoding="utf-8") == "新规则\n"

        # 一个锚点不命中时整文件保持原样：同文件的合法 pair 也不落盘
        changeset = write_changeset([
            {"file": "AGENTS.md", "kind": "replace", "pairs": [
                {"old": "新失败行。", "new": "不应落盘。"},
                {"old": "不存在的锚点。", "new": "x"},
            ]},
        ])
        run("--project", str(project), "--changeset", str(changeset), "--template-root", str(template), "--apply", code=2)
        assert "新失败行。" in (project / "AGENTS.md").read_text(encoding="utf-8")

        changeset = write_changeset([
            {"file": "docs/agents/dup.md", "kind": "replace", "pairs": [{"old": "锚点", "new": "y"}]},
        ])
        run("--project", str(project), "--changeset", str(changeset), "--template-root", str(template), "--apply", code=2)

        changeset = write_changeset([
            {"file": "AGENTS.md", "kind": "replace", "pairs": [{"old": "新删除行。", "new": "干跑。"}]},
        ])
        run("--project", str(project), "--changeset", str(changeset), "--template-root", str(template))
        assert "干跑。" not in (project / "AGENTS.md").read_text(encoding="utf-8")

        current = hashlib.sha256((project / "docs/agents/dup.md").read_bytes()).hexdigest()
        changeset = write_changeset([
            {"file": "docs/agents/dup.md", "kind": "sync",
             "source": "template/docs/agents/rules.md", "require_sha256": "0" * 64},
        ])
        run("--project", str(project), "--changeset", str(changeset), "--template-root", str(template), "--apply", code=2)
        changeset = write_changeset([
            {"file": "docs/agents/dup.md", "kind": "sync",
             "source": "template/docs/agents/rules.md", "require_sha256": current},
        ])
        run("--project", str(project), "--changeset", str(changeset), "--template-root", str(template), "--apply")
        assert (project / "docs/agents/dup.md").read_text(encoding="utf-8") == "新规则\n"

        changeset = write_changeset([
            {"file": "AGENTS.md", "kind": "add", "source": "template/docs/agents/rules.md"},
        ])
        run("--project", str(project), "--changeset", str(changeset), "--template-root", str(template), "--apply", code=2)

        stranger = root / "stranger"
        stranger.mkdir()
        run("--project", str(stranger), "--changeset", str(changeset), "--template-root", str(template), code=1)

    print("ok: apply_changeset smoke checks passed")


if __name__ == "__main__":
    main()
