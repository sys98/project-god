# project-template

新项目的开发约束模板。包含 AGENTS.md 体系（含交付阶段与延后加固边界）、docs/agents 规范、docs/deferred-hardening.md 延后加固清单、docs/architecture 与 docs/adr 骨架、GitLab 接入脚本和 CI 卫生检查。

本仓即 skill bundle：两个 skill 以 Codex 与 Claude 兼容的格式存放在 `.agents/skills/`，可同时安装到两个平台的用户级技能目录。

| Skill | 职责 |
| --- | --- |
| `new-project-from-idea` | 从一句话 idea 收敛需求、确认合同、生成并验证新项目基线；非空目标自动路由到 adopt-existing-project |
| `propagate-template-updates` | 模板规范更新后传播到所有已登记派生项目：逐文件锚点/sha 校验，fail-closed，分化项目只出差距报告 |
| `adopt-existing-project` | 旧项目改造：盘点现状、冲突逐个裁决、并入治理模板、按证据收口、产出优先级排序的差距报告 |

## 目录结构

```
project-template/
├── install.sh                 # 安装脚本：软链/复制 skill 到 Claude 与 Codex，迁移登记表
├── scripts/
│   └── check_pointers.py      # 校验全部文档中的 repo:// 指针与相对链接，防文档腐烂
├── .agents/skills/            # 两个 skill（Codex 的 agents/openai.yaml + 通用 SKILL.md）
│   ├── new-project-from-idea/
│   │   ├── SKILL.md           # 7 步主流程与触发条件
│   │   ├── scripts/scaffold.py        # 确定性拷贝器：拷 template/、替换占位符、剥离平台专属件
│   │   ├── scripts/test_scaffold.py
│   │   ├── references/template-closure.md  # 拷贝后的占位符收口清单与检查命令
│   │   └── evals/evals.json
│   └── propagate-template-updates/
│       ├── SKILL.md           # 5 步传播流程
│       ├── scripts/apply_changeset.py      # fail-closed 应用 changeset：锚点/sha 不满足即拒写
│       ├── scripts/test_apply_changeset.py
│       └── evals/evals.json
│   （adopt-existing-project 与两者并列，结构相同：SKILL.md + agents/openai.yaml + evals，无自有脚本，复用 scaffold.py）
└── template/                  # 治理模板本体，scaffold 的唯一拷贝源
    ├── AGENTS.md              # 单入口治理规则：阶段门控、授权边界、L1-L6 合同、fail-close
    ├── CLAUDE.md              # 只含 @AGENTS.md，Claude 入口指针
    ├── CONTEXT.md             # 项目统一语言：canonical term 词汇索引与词条
    ├── .gitlab-ci.yml         # GitLab CI 骨架（非 GitLab 项目生成时被剥离）
    ├── docs/
    │   ├── agents/            # 13 篇分领域规范：编码、架构、调试、流程、评审、写作、git 等
    │   ├── architecture/      # current-system-map.md 系统地图骨架
    │   ├── adr/               # 架构决策记录骨架
    │   └── deferred-hardening.md  # 延后加固清单（当前阶段登记，不占用工时）
    └── tools/
        ├── gitlab-api.sh      # GitLab API 封装脚本（凭证走 keychain）
        └── gitlab-api.test.sh
```

派生项目登记表不随仓分发：它是机器本地状态，位于 `${XDG_STATE_HOME:-~/.local/state}/project-template/initialized-projects.md`，由 install.sh 创建，`PROJECT_TEMPLATE_REGISTRY` 可覆盖。

## 安装为 skill

```bash
git clone https://github.com/sys98/project-god ~/.local/share/project-template
~/.local/share/project-template/install.sh
```

install.sh 把两个 skill 软链进 `~/.claude/skills/` 和 `~/.codex/skills/`，在任何目录下都能触发；软链指向本仓，`git pull` 后两个平台同时拿到更新。选项：`--copy`（复制快照而非软链）、`--claude-only` / `--codex-only`、`--uninstall`（只移除本脚本安装的内容）。

安装同时把派生项目登记表放到用户级状态目录 `${XDG_STATE_HOME:-~/.local/state}/project-template/initialized-projects.md`（旧仓根 `.agents/initialized-projects.md` 存在时自动迁移）。该文件是机器本地状态，不进任何 git 仓；可用 `PROJECT_TEMPLATE_REGISTRY` 环境变量覆盖位置。

## 从 Idea 开始：new-project-from-idea 执行后会发生什么

安装后在任意目录对 Claude 说“我有个 idea，想基于模板新建项目”（或 Codex 里用 `$new-project-from-idea`）。skill 按七步推进：

1. **定位**：解析模板根，确认目标目录状态（不存在/空/已有项目）。非空目录按 integrate 处理。
2. **收敛合同**：逐轮只问影响生成文件或架构的问题——产品定位、MVP 边界、技术栈、命名、目录、托管平台、可见性、验证命令。
3. **写入前确认**：给出紧凑合同与精确变更清单，等你一次明确确认。本地生成不自动授权 commit、远程建仓、push 或部署，每项外部变更单独授权。
4. **生成**：跑 `scaffold.py` 拷贝 `template/`、替换全部占位符，按平台剥离 GitLab 专属件；需要官方脚手架（如框架生成器）时先跑官方生成器再并入治理模板。
5. **模板收口**：按 `references/template-closure.md` 把定位、阶段、词汇、系统地图、技术栈规则替换为已确认事实，删除 `<initialization>` 节。
6. **配置工程技能**：调用 `$mattpocock-skills:setup-matt-pocock-skills` 补齐 issue tracker 与领域文档配置。
7. **验证并登记**：跑最小真实构建/测试，扫描残留占位符与失效平台引用，把项目登记进派生项目登记表（谱系 `直系`）。

交付说明会给出路径、合同、验证结果、Git 状态、跳过范围和剩余 Unknown。

## 同步模板变更：propagate-template-updates 执行后会发生什么

`template/` 的治理规范更新后，`$propagate-template-updates` 把变更传播到登记表里的所有派生项目，五步：

1. **构建 changeset**：默认范围是上次同步以来的 `template/` 提交；逐文件定单元类型——sync（整文件同步，sha 证明项目未本地改）、replace（逐 hunk 锚点替换）、add（模板新增文件）。
2. **校验项目集**：登记表里每个路径必须存在且含 AGENTS.md，缺失标 missing 跳过；写入前记录各项目的脏状态基线。
3. **分类**：每个单元判定 applicable 或 Needs-Decision（锚点不唯一、本地已分化），分化谱系项目只出差距报告。
4. **应用**：`apply_changeset.py` 先 dry-run 出计划，确认后加 `--apply` 写入；任一锚点失败该文件保持原样。
5. **验证、登记、报告**：逐项目 grep 旧措辞已消失、diff 只含 changeset 文件，然后在项目内提交（不 push），更新登记表「最近同步」列，输出逐项目报告。

新项目由 `$new-project-from-idea` 在交付时登记进清单；改造已有项目时建议登记为 `分化`，之后只收差距报告，由你决定每条规范是否采纳。

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

## 指令参考

会话触发（安装后任意目录可用）：

| 平台 | 新建项目 | 改造现有项目 | 传播模板更新 |
| --- | --- | --- | --- |
| Claude | `/new-project-from-idea` 或“我有个 idea…” | `/adopt-existing-project` 或“按模板规范改造这个项目” | `/propagate-template-updates` |
| Codex | `$new-project-from-idea` | `$adopt-existing-project` | `$propagate-template-updates` |

install.sh：

| 指令 | 作用 |
| --- | --- |
| `./install.sh` | 软链安装到 Claude 与 Codex，`git pull` 即更新 |
| `./install.sh --copy` | 复制快照安装，`template/` 随 skill 打包自包含 |
| `./install.sh --claude-only` / `--codex-only` | 只装一个平台 |
| `./install.sh --uninstall` | 移除本脚本安装的软链或带标记的副本，登记表保留 |

scaffold.py（skill 内部调用，也可手动）：

| 参数 | 说明 |
| --- | --- |
| `--destination` | 绝对路径；new 模式要求不存在或为空，integrate 要求已存在 |
| `--name` | 项目名，替换 `__PROJECT_NAME__` |
| `--forge` | `github` / `gitlab` / `none`；非 gitlab 剥离 GitLab 专属件 |
| `--forge-project` | `owner/project` 或 `group/subgroup/project` |
| `--forge-url` | gitlab 必填，必须 https |
| `--mode` | `new`（默认）/ `integrate`（改造已有项目，冲突即拒绝） |
| `--on-collision` | integrate 模式的冲突策略：`refuse`（默认，整体拒绝）/ `skip`（跳过并列出清单） |
| `--dry-run` | 只打印 copy/skip 计划，不写盘；改造前用它做冲突预演 |
| `--template-root` | 模板根覆盖，默认从脚本位置向上自动解析 |

环境变量：`PROJECT_TEMPLATE_REGISTRY`（登记表位置）、`GITLAB_API_BASE` / `GITLAB_KEYCHAIN_SERVICE`（GitLab endpoint 与凭证）、`XDG_STATE_HOME`（状态目录根）。

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
