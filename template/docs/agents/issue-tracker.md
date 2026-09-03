# Issue tracker

本仓的 issue 和 PRD 归__FORGE__，项目坐标 `__FORGE_PROJECT__`：

```text
__FORGE_PROJECT_URL__
```

## 约定

- **建 issue**：走平台 Web UI；任务明确批准自动化时才用 API。调试闭环（repo://docs/agents/debugging.md 第 8 节）与 wayfinding 认领所需的建单和打标即视为已批准，走平台封装脚本；仅批量建票（如 to-issues 拆分）需逐次确认。
- **读 issue**：按项目坐标打开对应 issue 页面。
- **列 issue**：项目 issue 列表按 label 过滤。
- **评论/关闭/打标**：用平台 issue 操作。
- **triage 标签**：五个 canonical 角色与本仓 label 的映射见 repo://docs/agents/triage-labels.md。

## 当 skill 说 "publish to the issue tracker"

在本仓 issue tracker 创建 issue。

## 当 skill 说 "fetch the relevant ticket"

按编号打开 issue，读描述、labels 和评论。

## 阻断与依赖

阻断语义以 issue body 里的 `Blocked by: #x #y` 文字为准，平台原生链接只做导航。判断“是否解除阻断”要读被引用 issue 的状态是否 closed。

GitLab CE 陷阱：issue link 只支持 `relates_to`（`blocks` / `is_blocked_by` 返回 400），阻断语义只能落在 body 文字。

## Wayfinding 编排

/wayfinder 地图与 ticket 在 issue tracker 的表达约定：

- **map（地图）**：一个 issue，label `wayfinder:map`。
- **子 ticket**：普通 issue，label `wayfinder:map-<map_iid>`（归属哪张图）+ `wayfinder:research|prototype|grilling|task`（类型）；body 首行写 `Map: #<map_iid>`。
- **查某图的 frontier**：按 label `wayfinder:map-<iid>` 过滤 open issue，再排除带 `wayfinder:claimed` 的、以及 body 中 `Blocked by` 未闭合的。阻断判定规则见上节。
- **认领**：会话开工前给 ticket 加 label `wayfinder:claimed`；做完在 resolution comment 写结论、close issue、回 map 的 Decisions-so-far 追加一行索引。
- `wayfinder:map-<iid>` 标签随地图创建即时新建；静态标签（map/claimed/四种类型）在初始化时预建。

## 程序化访问（API）

任务需要脚本化读写 issue/PRD/pipeline/runner 时（如批量建 ticket、查 CI），走本仓平台封装脚本。GitLab：repo://tools/gitlab-api.sh，凭证来源、endpoint 陷阱、`--data-urlencode` 写法和写后验证见 repo://docs/agents/gitlab-api-operations.md。其他平台：初始化时新建对应封装与文档，并在此登记坐标。
