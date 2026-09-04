#!/usr/bin/env bash
# Install project-template skills into Claude (~/.claude/skills) and Codex (~/.codex/skills).
# Default mode symlinks so template updates propagate through git pull; --copy installs a snapshot.
# Also migrates or creates the machine-local registry at ~/.local/state/project-template/.
# Usage: install.sh [--copy] [--claude-only | --codex-only] [--uninstall]
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILLS=(new-project-from-idea propagate-template-updates adopt-existing-project)
COPY=0
UNINSTALL=0
TARGETS=(claude codex)
COPY_MARKER=".project-template-bundle"

usage() {
    cat <<'EOF'
usage: install.sh [--copy] [--claude-only | --codex-only] [--uninstall]

  --copy         copy skill directories instead of symlinking (snapshot; no git-pull updates)
  --claude-only  install only into ~/.claude/skills
  --codex-only   install only into ~/.codex/skills
  --uninstall    remove only what this script installed (symlinks into this bundle, or marked copies)
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --copy) COPY=1 ;;
        --claude-only) TARGETS=(claude) ;;
        --codex-only) TARGETS=(codex) ;;
        --uninstall) UNINSTALL=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "error: unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

skills_dir_for() {
    case "$1" in
        claude) echo "$HOME/.claude/skills" ;;
        codex)  echo "$HOME/.codex/skills" ;;
    esac
}

# Absolute real path of a skill source dir inside this bundle.
skill_source() {
    echo "$BUNDLE_ROOT/.agents/skills/$1"
}

remove_one() {
    target_root="$1"; name="$2"; link="$target_root/$name"
    [ -e "$link" ] || [ -L "$link" ] || return 0
    if [ -L "$link" ]; then
        resolved="$(cd "$link" 2>/dev/null && pwd -P || true)"
        if [ "$resolved" = "$(skill_source "$name")" ]; then
            rm "$link"
            echo "removed symlink: $link"
        else
            echo "skip: $link is a symlink to somewhere else ($resolved)" >&2
        fi
    elif [ -d "$link" ] && [ -f "$link/$COPY_MARKER" ] && [ "$(cat "$link/$COPY_MARKER")" = "$BUNDLE_ROOT" ]; then
        rm -rf "$link"
        echo "removed copied dir: $link"
    else
        echo "skip: $link was not installed by this script" >&2
    fi
}

install_one() {
    target_root="$1"; name="$2"; link="$target_root/$name"; source="$(skill_source "$name")"
    if [ ! -f "$source/SKILL.md" ]; then
        echo "error: skill source missing: $source/SKILL.md" >&2
        return 1
    fi
    mkdir -p "$target_root"
    if [ -L "$link" ] && [ "$COPY" -eq 0 ]; then
        resolved="$(cd "$link" 2>/dev/null && pwd -P || true)"
        if [ "$resolved" = "$source" ]; then
            echo "already installed: $link"
            return 0
        fi
    fi
    if [ -e "$link" ] || [ -L "$link" ]; then
        echo "error: $link already exists and was not installed by this script; refusing to overwrite" >&2
        return 1
    fi
    if [ "$COPY" -eq 1 ]; then
        cp -R "$source" "$link"
        # Snapshot installs must be self-contained: bundle template/ inside the skill.
        cp -R "$BUNDLE_ROOT/template" "$link/template"
        echo "$BUNDLE_ROOT" > "$link/$COPY_MARKER"
        echo "copied: $link (with bundled template/)"
    else
        ln -s "$source" "$link"
        echo "linked: $link -> $source"
    fi
}

registry_path() {
    if [ -n "${PROJECT_TEMPLATE_REGISTRY:-}" ]; then
        echo "$PROJECT_TEMPLATE_REGISTRY"
    else
        echo "${XDG_STATE_HOME:-$HOME/.local/state}/project-template/initialized-projects.md"
    fi
}

migrate_registry() {
    registry="$(registry_path)"
    legacy="$BUNDLE_ROOT/.agents/initialized-projects.md"
    mkdir -p "$(dirname "$registry")"
    if [ -f "$registry" ]; then
        echo "registry exists: $registry"
    elif [ -f "$legacy" ]; then
        cp "$legacy" "$registry"
        echo "migrated registry: $legacy -> $registry"
    else
        cat > "$registry" <<'EOF'
# Initialized Projects

由 project-template 初始化的派生项目清单。它是 propagate-template-updates 的唯一项目源；新项目由 new-project-from-idea 在基线验证通过后登记。

## 维护规则

- 本文件是机器本地状态（含绝对路径），存放在用户级状态目录，不进任何 git 仓；其他机器各自维护本地副本。
- 路径必须绝对；项目根必须包含 AGENTS.md。
- 每次传播后更新「最近同步」列：模板 commit 加日期；未同步的分化项写 Needs-Decision 备注。
- 项目目录消失时把谱系标注为 missing，不删行。
- 谱系只取两值：直系（文档与模板同源，可锚点传播）或分化（本地词汇或结构已成体系，只出差距报告或最小适配）。
- 初始化日期取项目 AGENTS.md 首个提交日期；无证据时写 Unknown。

## 项目

| 项目 | 绝对路径 | 初始化日期 | 初始化模板 commit | 最近同步 | 谱系 |
| --- | --- | --- | --- | --- | --- |
EOF
        echo "created registry: $registry"
    fi
}

self_check() {
    failures=0
    for target in "${TARGETS[@]}"; do
        target_root="$(skills_dir_for "$target")"
        for name in "${SKILLS[@]}"; do
            if [ ! -f "$target_root/$name/SKILL.md" ]; then
                echo "check failed: $target_root/$name/SKILL.md not readable" >&2
                failures=1
            fi
        done
    done
    registry="$(registry_path)"
    [ -f "$registry" ] || { echo "check failed: registry missing: $registry" >&2; failures=1; }
    if command -v python3 >/dev/null 2>&1; then
        python3 "$BUNDLE_ROOT/scripts/check_pointers.py" || failures=1
    else
        echo "note: python3 not found; skipped check_pointers.py" >&2
    fi
    return "$failures"
}

if [ "$UNINSTALL" -eq 1 ]; then
    for target in "${TARGETS[@]}"; do
        target_root="$(skills_dir_for "$target")"
        for name in "${SKILLS[@]}"; do
            remove_one "$target_root" "$name"
        done
    done
    echo "uninstall done; registry kept at $(registry_path)"
    exit 0
fi

status=0
for target in "${TARGETS[@]}"; do
    target_root="$(skills_dir_for "$target")"
    for name in "${SKILLS[@]}"; do
        install_one "$target_root" "$name" || status=1
    done
done
[ "$status" -eq 0 ] || { echo "install incomplete; resolve the errors above and rerun" >&2; exit 1; }

migrate_registry

if self_check; then
    cat <<EOF

installed. trigger examples:
  Claude: /new-project-from-idea /adopt-existing-project /propagate-template-updates
  Codex:  \$new-project-from-idea \$adopt-existing-project \$propagate-template-updates
registry: $(registry_path)
EOF
else
    echo "install finished with failed checks; see above" >&2
    exit 1
fi
