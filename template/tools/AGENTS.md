# tools

L2 模块地图。规则见 repo://docs/agents/layer-contracts.md。

## 模块职责

- 拥有：仓库自动化脚本。
- 不拥有：业务能力、应用代码、CI 编排（repo://.gitlab-ci.yml）。

## 成员清单

- `gitlab-api.sh`：GitLab REST API 唯一脚本化 seam（L3-L5 头部）。凭证与 endpoint 陷阱见 repo://docs/agents/gitlab-api-operations.md。
- `gitlab-api.test.sh`：锁定 `create-project-runner` 的骨架期 `ci-internal` 固定合同，不访问真实 GitLab。

## 生成规则

- 脚本直接在仓库内运行，无构建、无产物入库。

## 反模式

- 在脚本里沉淀业务规则。
- 打印 token 或把凭证写入输出、日志。

## 测试锚点

- `bash tools/gitlab-api.test.sh`（`create-project-runner` 行为级）。
- CI hygiene job：`bash -n tools/gitlab-api.sh`（语法级，repo://.gitlab-ci.yml）。
