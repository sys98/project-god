# Current System Map

Status: bootstrap

本文件描述当前可验证的系统边界、模块所有权、依赖方向和验证入口。不要写目标愿景冒充现状。

## 当前事实

- 仓库：__PROJECT_NAME__。
- 阶段：项目技术基础初始化。交付阶段与延后边界由根 repo://AGENTS.md `<stage>` 拥有。
- 业务目标：Unknown。
- 技术栈：Unknown。
- 运行入口：Unknown。
- 部署拓扑：Unknown。
- 持久状态 owner：Unknown。
- 外部系统：Unknown。

当前只有开发约束和文档骨架。没有可验证的应用模块。

## 链路

端到端业务链路：Unknown。当前唯一工具链路：

    agent -> tools/gitlab-api.sh -> GitLab REST API（issue / runner / pipeline 读写）

## 不变量

任何实现不能破坏的根约束：

- GitLab token 仅经 stdout 输出本体，永不写入日志与错误输出（repo://tools/gitlab-api.sh [L4] gitlab_token）。

## 目标记录格式

新模块首次落地时，补充以下信息：

| Module | Owns | Does not own | Public interface | Depends on | Verification |
| --- | --- | --- | --- | --- | --- |
| Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |

同时记录依赖方向：

    caller -> public interface -> owning module -> external seam

缓存、日志、UI 和 read model 只能从 canonical owner 读取。它们不能反向写入 owner。

## 更新触发

以下变化必须更新本文件：

- 项目目标或顶层模块变化。
- 新增或删除服务、应用、数据库或外部系统。
- 状态所有权、跨模块依赖或公开入口变化。
- 架构迁移阶段、切换顺序或兼容边界变化。

难回退或存在真实取舍的决定同时写入 repo://docs/adr/。

## 验证

项目尚无构建、测试和运行命令。状态为 Unknown。

技术栈落地后，从 package manifest、构建配置和 CI 发现真实命令，并把稳定入口写入最近的 AGENTS.md。不要在这里复制可直接从配置读取的完整脚本清单。

## PROTOCOL

根合同（本文件「当前事实」「链路」「不变量」）变化时同步：

- repo://CONTEXT.md（统一语言）。
- 根 repo://AGENTS.md（指针与触发）。
- 命中模块的 AGENTS.md（L2）与文件内 L3-L6 合同。
- 架构取舍写 repo://docs/adr/ 新 ADR，不改写已 accepted 的结论。
