---
name: adopt-existing-project
description: Adopt the project-template governance standards into an existing project without overwriting its files — survey current state, adjudicate collisions, integrate the template, close placeholders from evidence, and produce a prioritized gap report. Use when the user wants to 改造/接入/治理 an existing project with this template; do not use for scaffolding a new project (use new-project-from-idea) or for propagating template updates (use propagate-template-updates).
---

# Adopt Existing Project

Bring an existing project under this template's governance. The project's own code, history, and documents are the truth; the template adapts to them, never the reverse. Stop at a verified adoption unless the user also asks for remediation work.

## 1. Survey the current state

Read before proposing anything. Record every claim with an evidence coordinate (file, command output); mark the rest Unknown.

- stack, runtime entry, build/test commands that actually run;
- existing docs: AGENTS.md, CLAUDE.md, README, docs/, ADRs;
- CI configuration and forge platform (GitLab/GitHub/none);
- git state: branch, dirty files, remote coordinates;
- test layout and the smallest runnable check;
- existing business vocabulary worth seeding into CONTEXT.md.

Completion criterion: a written survey covers every dimension above, each with evidence or Unknown.

## 2. Rehearse collisions

Run a dry-run to enumerate exactly what the template would touch:

```bash
python3 <skill-dir>/../new-project-from-idea/scripts/scaffold.py \
  --mode integrate --on-collision skip --dry-run \
  --destination /absolute/path/to/project \
  --name project-name --forge <github|gitlab|none> [--forge-project ...] [--forge-url ...]
```

Every `skip:` line is a decision for the user, one of three: keep mine (template file skipped), take template (move the existing file to `<project>/.adoption-backup/` preserving relative paths, then it is no longer a collision), or merge manually (skip now, merge by hand after integration).

Completion criterion: every collision holds an explicit user decision; none is silently skipped.

## 3. Confirm the write

Show the survey summary, the collision decisions, and the exact mutation set: files copied, files moved to `.adoption-backup/`, directories created. Ask for one explicit confirmation before any write.

Local integration authority does not include commit, push, remote changes, dependency changes, or application-code edits. Obtain separate authority immediately before each.

Completion criterion: the user has approved one exact mutation set.

## 4. Integrate

Move user-approved replacements into `.adoption-backup/` first, then rerun without `--dry-run`:

```bash
python3 <skill-dir>/../new-project-from-idea/scripts/scaffold.py \
  --mode integrate --on-collision skip \
  --destination /absolute/path/to/project \
  --name project-name --forge <...> [--forge-project ...] [--forge-url ...]
```

The script refuses broad paths and never overwrites an existing file; skipped files are printed and must match the step-2 decisions exactly. Investigate any mismatch before continuing.

Completion criterion: the project contains the governance template, every pre-existing file is byte-identical, and the printed skip list matches the adjudicated set.

## 5. Close from evidence

Follow [../new-project-from-idea/references/template-closure.md](../new-project-from-idea/references/template-closure.md), but source every field from the step-1 survey, not from defaults:

- `AGENTS.md` `<project>`: the real one-sentence position and stack.
- `AGENTS.md` `<stage>`: judge the project's actual stage from evidence (external traffic, commitments); when unclear, ask — this decision changes how work is scheduled.
- `CONTEXT.md`: seed 词汇索引 with the domain terms the code already uses.
- `docs/architecture/current-system-map.md`: the modules that exist today, not the target design.
- `docs/agents/coding-standards.md` section 10: rules for the stack actually in use.

Delete the `<initialization>` section only when its checklist is complete. Keep honest Unknowns.

Completion criterion: no bootstrap placeholder remains and every closed fact cites survey evidence.

## 6. Gap report

Walk the `docs/agents/` standards against the observed project state and produce a prioritized gap list. For each gap: the standard it violates (file + section), the observed evidence, and severity per `docs/agents/quality-standards.md` section 2.

- Gaps blocking current correctness (security holes, data corruption, broken workflows) are reported for immediate fixing — they do not enter any deferral list.
- Deferrable gaps are registered in `docs/deferred-hardening.md`.
- The report proposes an adoption order (typically: git-branching, development-workflow, debugging first; the rest land through daily work).

The report never claims the codebase was retrofitted. Standards constrain changes made after adoption.

Completion criterion: every one of the 13 standards documents is either confirmed met with evidence or appears in the gap list.

## 7. Verify and register

Run the project's own smallest build/test command (from step 1, not invented) and record the observed result. Scan for unresolved placeholders and stale forge references. Confirm `git status` shows only template additions and `.adoption-backup/`.

Register the project in the machine-local initialized-projects registry (resolution order: `$PROJECT_TEMPLATE_REGISTRY`, then `${XDG_STATE_HOME:-~/.local/state}/project-template/initialized-projects.md`), with lineage `分化` by default — adopted projects keep their own vocabulary and receive gap reports rather than mechanical edits. Switch to `直系` only when the user explicitly wants anchored propagation.

Completion criterion: the handoff states what was integrated, the collision outcomes, verification evidence, the gap report location, git state, and remaining Unknowns; the registry entry exists.
