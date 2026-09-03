# Template closure

Read this only after `scripts/scaffold.py` has copied the governance template.

## Universal closure

Use the confirmed project contract to update:

- `AGENTS.md` `<project>`: one-sentence position, real stack, and stable verification entry.
- `AGENTS.md` `<stage>`: confirmed stage name, this project's core responsibilities, and exit signals. New projects normally keep the rapid-iteration default.
- `docs/deferred-hardening.md`: clear the example row. Leave it empty until real work produces entries.
- `CONTEXT.md`: product boundary and canonical terms; register each confirmed term in 词汇索引 with its detail entry; remove bootstrap vocabulary that does not describe the product.
- `docs/architecture/current-system-map.md`: current modules, state owner, external seams, runtime entry, and verified commands.
- `docs/agents/coding-standards.md` section 10: only stack rules that configuration cannot express.
- `docs/agents/issue-tracker.md` and `docs/agents/debugging.md`: selected forge language and live coordinates.
- `README.md`: purpose, scope, requirements, run/build/test commands, and remote status.

Delete the `<initialization>` section from `AGENTS.md` only when every applicable item is complete. Do not create an ADR for a cheap, reversible bootstrap choice.

## Forge branches

### GitHub

The copier removes GitLab-only scripts, operations docs, and CI. Rewrite remaining GitLab wording in `AGENTS.md`, the system map, issue tracker, and debugging guide. Record GitHub Actions as absent until a real workflow exists. Use `gh` only under explicit remote-write authority.

### GitLab

Keep `.gitlab-ci.yml`, `tools/gitlab-api.*`, and `docs/agents/gitlab-api-operations.md`. Verify the configured GitLab host and credential source; the current template defaults are company-specific. Do not claim runner or pipeline readiness without live readback.

### No forge

The copier removes GitLab-only artifacts. Mark remote coordinates and CI as Unknown or absent. Keep local Git actions separate from later remote selection.

## Closure checks

Run from the generated project root:

```bash
rg -n '__[A-Z0-9_]+__' . --hidden --glob '!.git/**'
rg -n 'GitLab|gitlab|\.gitlab-ci|tools/gitlab' AGENTS.md README.md CONTEXT.md docs 2>/dev/null
git status --short --branch 2>/dev/null || true
```

For GitHub or no-forge projects, the GitLab scan must be empty unless a retained historical note explicitly needs it. For GitLab projects, every match must point to the selected live platform rather than an unverified default.
