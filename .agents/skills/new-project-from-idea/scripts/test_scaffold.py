#!/usr/bin/env python3
"""Runnable smoke checks for scaffold.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("scaffold.py")


def run(*arguments: str, succeeds: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) == succeeds, result.stdout + result.stderr
    return result


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="project-template-test-") as temporary:
        root = Path(temporary)

        github = root / "github-app"
        run(
            "--destination", str(github),
            "--name", "github-app",
            "--forge", "github",
            "--forge-project", "owner/github-app",
        )
        assert (github / "AGENTS.md").is_file()
        assert "github-app" in (github / "AGENTS.md").read_text(encoding="utf-8")
        assert not (github / ".gitlab-ci.yml").exists()
        assert not (github / "tools").exists()

        integrated = root / "generated-app"
        integrated.mkdir()
        application_file = integrated / "package.json"
        application_file.write_text('{"private":true}\n', encoding="utf-8")
        run(
            "--mode", "integrate",
            "--destination", str(integrated),
            "--name", "generated-app",
            "--forge", "none",
        )
        assert application_file.read_text(encoding="utf-8") == '{"private":true}\n'
        assert (integrated / "CONTEXT.md").is_file()
        run(
            "--mode", "integrate",
            "--destination", str(integrated),
            "--name", "generated-app",
            "--forge", "none",
            succeeds=False,
        )

        gitlab = root / "gitlab-app"
        run(
            "--destination", str(gitlab),
            "--name", "gitlab-app",
            "--forge", "gitlab",
            "--forge-project", "group/gitlab-app",
            "--forge-url", "https://gitlab.example.com/group/gitlab-app",
        )
        assert (gitlab / ".gitlab-ci.yml").is_file()
        assert (gitlab / "tools/gitlab-api.sh").is_file()
        assert "__PROJECT_NAME__" not in (gitlab / "tools/gitlab-api.sh").read_text(encoding="utf-8")

    print("ok: scaffold smoke checks passed")


if __name__ == "__main__":
    main()
