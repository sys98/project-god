---
name: new-project-from-idea
description: Turn an early software idea into a confirmed project contract, adapt this repository's template, and generate a verified project at the user's chosen local path. Use when the user says they have an idea and wants to start, create, or scaffold a new project from project-template; do not use for feature work in an already initialized project.
---

# New Project from Idea

Produce a safe, minimal project baseline. The template supplies development governance; the chosen platform supplies application code. Stop at a verified baseline unless the user also asks for feature implementation.

## 1. Locate

Resolve the repository root from this skill's path and verify that `template/` exists. The skill may be installed through a symlink (user-level install into `~/.claude/skills` or `~/.codex/skills`); resolve the real path before deriving the root. The bundled scripts already do this via `Path(__file__).resolve()`. Read the root `README.md`, `template/AGENTS.md`, `template/CONTEXT.md`, and `template/docs/architecture/current-system-map.md`.

Inspect likely parent directories and the requested destination before proposing creation. Classify the destination as missing, empty, or an existing project. Treat a non-empty destination as integration work, not a new scaffold.

Completion criterion: the live template root and one exact absolute destination are known, and every existing target path is accounted for.

## 2. Shape the contract

Start from facts already supplied by the user. Ask one decision question per turn only when its answer changes generated files or architecture. Put the recommended option first and continue safe read-only discovery between answers.

Confirm or mark Unknown:

- one-sentence product position, target user, problem, and first observable success;
- MVP capabilities, explicit exclusions, state owner, persistence, and data-loss boundaries;
- target platform, runtime, framework, and the nearest reusable open-source or native mechanism;
- product name, repository slug, and collision check when public naming matters;
- absolute destination, forge coordinates, visibility, local distribution, and verification command;
- whether the requested outcome is governance-only or the smallest runnable application baseline.

For animal-IP brands, use `动物词根 + 三音节 + 尾音重复 + 开口元音` (`animal root + three syllables + repeated ending + open vowels`) as the naming heuristic. Show the root and syllable split for each candidate, keep it independently pronounceable, and collision-check only finalists.

Research current frameworks or name collisions only when the decision depends on current external facts. Prefer primary sources and compare the fewest viable candidates. Keep unsupported claims Unknown.

Completion criterion: every field that affects scaffolding is confirmed; remaining Unknowns cannot change the initial file tree.

## 3. Confirm the write

Show a compact contract and the exact mutations: destination, scaffold mode, platform generator, forge branch, files removed, and Git actions. Ask for one explicit confirmation before any write.

Local generation authority does not include commit, remote creation, push, PR, deployment, or secret handling. Obtain separate authority immediately before each external mutation.

Completion criterion: the user has approved one exact destination and mutation set.

## 4. Generate

Use the deterministic copier at `scripts/scaffold.py`.

For an empty destination:

```bash
python3 <skill-dir>/scripts/scaffold.py \
  --destination /absolute/path/to/project \
  --name project-name \
  --forge github \
  --forge-project owner/project
```

If an official framework generator requires an empty directory, run it first, then merge the governance template without overwriting application files:

```bash
python3 <skill-dir>/scripts/scaffold.py \
  --mode integrate \
  --destination /absolute/path/to/project \
  --name project-name \
  --forge github \
  --forge-project owner/project
```

Supported forge values are `github`, `gitlab`, and `none`. For GitLab, also pass the full project URL with `--forge-url`. The script refuses broad paths, non-empty new targets, and integration collisions.

Use the official platform generator or native project format for the smallest runnable baseline selected in the contract. Add no speculative services, extension points, or feature backlog.

Completion criterion: the destination contains the application baseline plus one non-overlapping copy of the governance template.

## 5. Close the template

Read [references/template-closure.md](references/template-closure.md) after copying. Replace bootstrap facts with the confirmed contract, remove irrelevant platform artifacts, and delete the generated `AGENTS.md` `<initialization>` section only after its checklist is complete.

Keep each fact in one authoritative document. Leave still-valid Unknowns explicit. Never copy credentials or machine-specific secrets.

Completion criterion: no bootstrap placeholder remains, active documents describe the selected forge and real stack, and documented commands match the generated project.

## 6. Configure engineering skills

From the generated project, invoke `$mattpocock-skills:setup-matt-pocock-skills`. Follow its prompt-driven explore, present, confirm, and write flow; reuse the confirmed forge and domain facts without silently answering choices for the user.

That skill is explicit-only. If the host cannot chain it from this skill, ask the user to invoke it once, then resume this workflow. Keep its instructions in that skill instead of duplicating them here.

Completion criterion: the setup skill reports completion and the generated repository records its issue tracker and domain-doc layout.

## 7. Prove the baseline

Run the smallest real build, test, or launch check for the selected stack. Also scan for unresolved placeholders and stale forge references. Inspect `git status` and preserve unrelated files.

Initialize local Git only when approved. Commit or publish only under separate explicit authority.

Register the project in the machine-local initialized-projects registry, resolved in this order: `$PROJECT_TEMPLATE_REGISTRY`, then `${XDG_STATE_HOME:-~/.local/state}/project-template/initialized-projects.md`. Create it with the standard header when missing (install.sh already does this on install). Record: name, absolute path, initialization date, the current template commit, and lineage `直系`. The registry is the only project source `$propagate-template-updates` consults when template standards later change.

Completion criterion: the baseline runs or builds, every check has an observed result, the handoff states the path, contract, validation, Git state, skipped scope, and remaining Unknowns, and the project is registered.
