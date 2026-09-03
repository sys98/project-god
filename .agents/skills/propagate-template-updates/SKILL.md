---
name: propagate-template-updates
description: Propagate a template governance change from this repository into every initialized derived project, using fail-closed anchored edits driven by the machine-local initialized-projects registry. Use when template/ standards files (AGENTS.md, docs/agents/*) changed and derived projects need the same update, or when asked which projects were initialized from this template. Do not use for initial scaffolding of a new project or for feature work inside a derived project.
---

# Propagate Template Updates

Sync one template change into every derived project recorded in the initialized-projects registry. The registry is machine-local state, resolved in this order: `$PROJECT_TEMPLATE_REGISTRY`, then `${XDG_STATE_HOME:-~/.local/state}/project-template/initialized-projects.md`. If it is missing, create it with the standard header before registering (see install.sh). Judgment decides what the change is; mechanism decides what may be written: every write is fail-closed behind a byte-proof or an exactly-one anchor. A diverged file is reported, never force-written.

## 1. Build the changeset

Default scope: template commits since the project's last-sync entry (`git log --oneline <since>..HEAD -- template/`, run in the bundle repository this skill resolves to); otherwise the commit or change the user names. If the bundle has no git history (fresh `git init`, snapshot copy), the scope is the change the user names.

For each changed template file, choose the unit kind:

- **sync** when the derived file should be byte-identical to the template version. Prove the project's current file equals the pre-change version: `git show <commit>~1:template/<file> | shasum -a 256` must equal `shasum -a 256 <project>/<file>`. Enqueue the proven sha as `require_sha256`.
- **replace** when the file carries per-project content (AGENTS.md, CONTEXT.md) or local edits. Take each hunk as an exact old→new pair, old verbatim from the pre-change version.
- **add** when the template gained a file the project lacks.

A propagated line that adds a `repo://` pointer rots when the project lacks the target: confirm the target exists there, add that file in the same changeset, or rewrite the line without the pointer.

Completion criterion: every changed template file maps to units, and every old anchor and sha is proven against the pre-change template version.

## 2. Verify the project set

Read the initialized-projects registry (resolution order in the header). Each path must exist and contain `AGENTS.md`; a missing path is reported and skipped, not searched for. A user-named project absent from the registry gets verified the same way, then appended.

Run `git -C <project> status --short` before any write and record the output: pre-existing dirt must survive byte-identical and be reported as pre-existing.

Completion criterion: every candidate project is classified reachable or missing, and each reachable project's dirty baseline is recorded.

## 3. Classify every unit

- sync/add preconditions hold (sha proven, target absent) → applicable.
- Every replace anchor occurs exactly once in the project file → applicable.
- Anything else → Needs-Decision: skip the file, record which anchors missed or what local text diverged.

Projects marked 分化 in the registry get a gap report instead of mechanical edits. Adapt at most one minimal line per document, in the project's own vocabulary, only where a natural home exists (example: a local `fail closed` error section). Dated records (`docs/adr/*`, research logs) are history and keep their wording.

Completion criterion: every unit in every project holds an apply verdict or a Needs-Decision verdict with evidence.

## 4. Apply

Write the changeset JSON to a scratch path outside the derived project, then:

```bash
python3 <skill-dir>/scripts/apply_changeset.py --project /abs/path --changeset /tmp/changeset.json
```

Read the printed plan; rerun with `--apply` only when the plan matches the step-3 verdicts. The script refuses unsafe units (exit 2), keeps each file atomically untouched when any of its anchors fail, and reports per unit. Repeat per project.

Completion criterion: every project's run ends with each unit applied or explicitly refused.

## 5. Verify, register, report

Per project: grep the old wording (gone from `AGENTS.md` and `docs/agents/`; ADRs untouched), and compare `git status` against the recorded baseline — only changeset files may differ. Run the project's own pointer or doc check when it has one. After verification, invoke the git-commit workflow in that project: stage the changeset files explicitly in a mixed tree, run the smallest feasible check, commit with a Conventional Commit subject and an audit body covering problem, change, reason, verification, and risk, and do not push or merge.

Update the registry's 最近同步 column: template commit and date, or the Needs-Decision note. Leave pre-existing dirt and unrelated files untouched in each project.

Completion criterion: the report covers, per project — applied files, refused units with evidence, preserved pre-existing dirt, commit hash when a commit was made, and the registry update.
