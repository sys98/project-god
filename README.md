# project-template

新项目的开发约束模板。包含 AGENTS.md 体系（含交付阶段与延后加固边界）、docs/agents 规范、docs/deferred-hardening.md 延后加固清单、docs/architecture 与 docs/adr 骨架、GitLab 接入脚本和 CI 卫生检查。

本仓即 skill bundle：两个 skill 以 Codex 与 Claude 兼容的格式存放在 `.agents/skills/`，可同时安装到两个平台的用户级技能目录。

| Skill | 职责 |
| --- | --- |
| `new-project-from-idea` | 从一句话 idea 收敛需求、确认合同、生成并验证新项目基线；`--mode integrate` 改造已有项目（只并入治理模板，不覆盖已有文件） |
| `propagate-template-updates` | 模板规范更新后传播到所有已登记派生项目：逐文件锚点/sha 校验，fail-closed，分化项目只出差距报告 |

## 安装为 skill

```bash
git clone https://github.com/sys98/project-god ~/.local/share/project-template
~/.local/share/project-template/install.sh
```

install.sh 把两个 skill 软链进 `~/.claude/skills/` 和 `~/.codex/skills/`，在任何目录下都能触发；软链指向本仓，`git pull` 后两个平台同时拿到更新。选项：`--copy`（复制快照而非软链）、`--claude-only` / `--codex-only`、`--uninstall`（只移除本脚本安装的内容）。

安装同时把派生项目登记表放到用户级状态目录 `${XDG_STATE_HOME:-~/.local/state}/project-template/initialized-projects.md`（旧仓根 `.agents/initialized-projects.md` 存在时自动迁移）。该文件是机器本地状态，不进任何 git 仓；可用 `PROJECT_TEMPLATE_REGISTRY` 环境变量覆盖位置。

## 从 Idea 开始

安装后在任意目录对 Claude 说“我有个 idea，想基于模板新建项目”（或 Codex 里用 `$new-project-from-idea`）。skill 会引导需求收敛、目录与托管平台确认、模板适配、最小工程生成和验证。

项目生成后，流程会调用 `$mattpocock-skills:setup-matt-pocock-skills`，补齐工程技能需要的 issue tracker 与领域文档配置。

它在确认写入前只做调查。创建本地项目不自动授权 commit、远程建仓、push 或部署。

## 同步模板变更

`template/` 的治理规范更新后，`$propagate-template-updates` 把变更传播到登记表里的所有派生项目：逐文件锚点或 sha 校验，fail-closed，分化项目只出差距报告。新项目由 `$new-project-from-idea` 在交付时登记进清单。

## 用法（免安装手动路径）

```bash
python3 /path/to/project-template/.agents/skills/new-project-from-idea/scripts/scaffold.py \
  --destination /absolute/path/to/new-app \
  --name new-app \
  --forge gitlab \
  --forge-project junbo/official/new-app \
  --forge-url https://192.168.121.43/junbo/official/new-app
```

scaffold.py 把 `template/` 拷入目标目录并替换全部占位符；`--forge github` 或 `none` 时自动移除 GitLab 专属件（`.gitlab-ci.yml`、`tools/gitlab-api.*`、`docs/agents/gitlab-api-operations.md`）。改造已有项目用 `--mode integrate`，只并入治理模板、不覆盖已有文件，冲突时拒绝。参数与分支细节见 `.agents/skills/new-project-from-idea/SKILL.md` 第 4 节。

公司 GitLab host（`192.168.121.43`）和 keychain 记录（`JUNBO_GITLAB_API_TOKEN`）是公司级常量，直接保留。换环境时改 `tools/gitlab-api.sh` 顶部的默认值，或用 `GITLAB_API_BASE` / `GITLAB_KEYCHAIN_SERVICE` 环境变量覆盖。

## 验证

```bash
python3 .agents/skills/new-project-from-idea/scripts/test_scaffold.py
python3 .agents/skills/propagate-template-updates/scripts/test_apply_changeset.py
python3 scripts/check_pointers.py
```

## 初始化后必做

1. `git init`，首次提交按 AGENTS.md 约束只 stage 语义相关路径。
2. 补 AGENTS.md 里的一句话项目定位。
3. `tools/gitlab-api.sh token-check` 验证凭证链路。
4. 需要 CI runner 时按 `docs/agents/gitlab-api-operations.md` 第 8 节创建。
