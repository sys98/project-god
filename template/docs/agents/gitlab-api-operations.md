# GitLab API 链路操作指南

本文记录用 GitLab REST API 程序化读写本仓 issue/PRD 的可操作链路，补足
`docs/agents/issue-tracker.md`（约定层）缺的执行细节。约定层说"用什么"，
本文说"怎么调通"。

适用场景：Agent 需要程序化创建/更新 PRD、批量发布拆分 issue、读取 work item
内容做拷问或拆分（如 grill-with-docs / to-prd / to-issues 等 skill）。

---

## 1. 凭证：token 在 macOS keychain

GitLab API token 不在 `.netrc`，机器上也没有 `glab` CLI。首选存在 macOS
keychain，脚本也允许用环境变量临时覆盖。

```bash
GITLAB_TOKEN=$(security find-generic-password -a simon -s JUNBO_GITLAB_API_TOKEN -w)
```

- `-a simon`：account（账户名）；旧机器可能仍是 `dimon`
- `-s JUNBO_GITLAB_API_TOKEN`：service（服务名，即这条 keychain 记录的标识）
- `-w`：只输出密码值本身

取到后用 `--header "PRIVATE-TOKEN: $GITLAB_TOKEN"` 传给 curl。**不要把 token
值回显到对话或日志**；只引用 keychain 记录名。

首选脚本入口是 `repo://tools/gitlab-api.sh`。Agent 和自动化脚本应优先调用它，
不要每次手写 token 查找和项目 URL：

```bash
tools/gitlab-api.sh token-check
tools/gitlab-api.sh project GET 'issues/182'
tools/gitlab-api.sh project GET 'pipelines?ref=main'
tools/gitlab-api.sh project-runners
tools/gitlab-api.sh runners-all
```

脚本按顺序读取 `GITLAB_TOKEN`、`GITLAB_PRIVATE_TOKEN`，最后回退到 keychain 记录；
未显式设置 `GITLAB_KEYCHAIN_ACCOUNT` 时会依次尝试 `dimon`、`simon`。可用
`GITLAB_KEYCHAIN_ACCOUNTS` 覆盖 fallback 列表。脚本只把 token 放进
`PRIVATE-TOKEN` header，不打印 token。

## 2. 基础 URL 与证书

- API base：`https://192.168.121.43/api/v4`
- 项目标识（URL-encoded path）：`__GITLAB_PROJECT_ENCODED__`
  （即 `__GITLAB_PROJECT__`，斜杠编码为 `%2F`）
- 内网自签证书：curl 必须加 `-k`（`--insecure`）跳过证书校验，否则连接失败。
- 直接 GET 网页 URL（`/-/work_items/182`）会 302 跳转到 `users/sign_in`，
  **拿不到内容**——必须走 API + token，不要 curl 网页路径。

## 3. ⚠️ 端点陷阱：work_items vs issues

浏览器地址栏是 `.../-/work_items/182`，但 **REST API v2 的 `work_items/<iid>`
端点会返回 404**。程序化读写要用 **`issues/<iid>`** 端点：

```bash
# 错误：404 Not Found
.../api/v4/projects/<proj>/work_items/182
# 正确：200
.../api/v4/projects/<proj>/issues/182
```

GitLab 的 "work item" 是 issue 的 UI 新名，底层仍是 issue 资源。除非确认服务端
开了 work items GraphQL/REST 新接口，否则一律走 `issues` 端点。

## 4. 常用调用

所有调用先取 token（见 §1），下面省略。`BASE` 与项目变量：

```bash
GITLAB_TOKEN=$(security find-generic-password -a simon -s JUNBO_GITLAB_API_TOKEN -w)
BASE="https://192.168.121.43/api/v4/projects/__GITLAB_PROJECT_ENCODED__/issues"
```

### 读一个 issue

```bash
curl -sk --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$BASE/182"
```

返回 JSON 含 `title` / `description` / `labels` / `state` / `web_url` /
`updated_at` 等。`description` 是 Markdown 正文。

### 创建 issue

正文用 `--data-urlencode "description@<文件路径>"` 从文件读，**不要把长
Markdown 直接拼进命令行**（全角标点、换行、`$` 等会被 shell 破坏）：

```bash
curl -sk --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --data-urlencode "title=标题" \
  --data-urlencode "description@/tmp/body.md" \
  --data-urlencode "labels=ready-for-agent" \
  "$BASE"
```

成功返回 HTTP 201，JSON 里 `iid` 是新 issue 的内部编号。

### 覆盖更新 issue（PRD 重写）

```bash
curl -sk --request PUT \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --data-urlencode "title=新标题" \
  --data-urlencode "description@/tmp/new_body.md" \
  --data-urlencode "labels=ready-for-agent" \
  "$BASE/182"
```

成功返回 HTTP 200。`description` 是**整体覆盖**，不是追加。

## 5. 转义与正文：用文件，不要拼命令行

本仓 PRD/issue 正文含大量全角标点（`：｜、（）`）、Markdown 代码块、JSON
片段。这些直接进 shell 命令行会被截断或污染。**始终把正文写到临时文件，再用
`--data-urlencode "description@文件"` 读**。这是这条链路最容易踩的坑。

## 6. 批量发布 + 依赖引用顺序

发布有依赖关系的多个 issue（如 to-issues 拆分的 vertical slices）时：

1. **先发 blocker，拿到真实 iid**，再发依赖它的 issue，在 body 的
   "Blocked by" 里引用真实 iid（如 `#183`）。不要赌 iid 连号。
2. 若某 issue 引用了尚未创建的 iid，先把被引用的发出来确认 iid，再发引用方。
3. 用一个 `post()` shell 函数顺序发同一依赖层的多个 issue，立即解析返回的
   `iid` 校验。

### "Blocked by" 是文字，不是结构化依赖

上述做法把依赖写在 issue **body 的文字**里。GitLab 原生的结构化依赖
（work item blocking links）是另一套端点，需要单独建。如果调度工具
（如并行开发子线程）读 body 文字即可，文字够用；若依赖 GitLab 原生依赖图，
需另行建 link。建之前先确认服务端版本支持。

## 7. 校验

写操作后**重新 GET 一次**确认服务端实际落库（不要只信 POST/PUT 的本地返回）：

```bash
curl -sk --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$BASE/182" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      print(d['title'], d['labels'], d['updated_at']); \
      print('len', len(d['description']))"
```

校验点：title / labels 是否对、description 长度是否合理、关键决策句是否在正文里。

## 8. Runner 自动化：只注册 ci-internal

骨架期只启用一个项目 runner：`__PROJECT_NAME__-ci`。它只接收带 `ci-internal` tag 的
检查任务，不承担构建和发布。不要注册 `staging-internal` 或
`production-internal`。GitLab runner 操作统一走
`repo://tools/gitlab-api.sh`，不要增加第二套 bootstrap 脚本。

GitLab 17+ 使用 `POST /user/runners` 创建 runner 配置。命令会返回一次性的 runner
authentication token（执行器认证令牌）：

```bash
umask 077
tools/gitlab-api.sh create-project-runner > /tmp/__PROJECT_NAME__-runner.json
chmod 600 /tmp/__PROJECT_NAME__-runner.json
```

固定配置为 `description=__PROJECT_NAME__-ci`、`tag_list=ci-internal`、
`access_level=not_protected`、`locked=true`、`run_untagged=false`。输出 JSON 含一次性
`token`。不要把文件内容或 token 发到聊天、CI log 或 commit。若旧记录的 token 已
丢失，先用 `project-runners` 找到旧 id；仅在准备立即重新注册时删除并重建：

```bash
tools/gitlab-api.sh project-runners
tools/gitlab-api.sh raw DELETE 'runners/<旧 runner id>'
```

在 runner 服务器安装并启动 GitLab Runner 后，读取 token 时关闭终端回显，再注册
Docker executor。`locked`、`run_untagged` 和 tag 由创建 API 管理，不写入
`config.toml`：

```bash
read -rsp 'runner authentication token: ' RUNNER_TOKEN && printf '\n'
sudo gitlab-runner register \
  --non-interactive \
  --url 'https://192.168.121.43' \
  --token "$RUNNER_TOKEN" \
  --name '__PROJECT_NAME__-ci' \
  --executor 'docker' \
  --docker-image 'node:22-bookworm-slim' \
  --tls-ca-file '/etc/gitlab-runner/certs/192.168.121.43.crt'
unset RUNNER_TOKEN
sudo gitlab-runner verify
```

注册后从 GitLab Source of Truth 读回。第一个断言同时确保项目下没有第二个 runner；
第二个断言核对项目锁定、tag 和未打 tag 任务策略：

```bash
RUNNER_ID="$(
  tools/gitlab-api.sh project-runners |
    python3 -c 'import json, sys
runners = json.load(sys.stdin)
assert len(runners) == 1, runners
assert runners[0]["description"] == "__PROJECT_NAME__-ci", runners[0]
print(runners[0]["id"])'
)"

tools/gitlab-api.sh raw GET "runners/$RUNNER_ID" |
  python3 -c 'import json, sys
runner = json.load(sys.stdin)
assert runner["runner_type"] == "project_type", runner
assert runner["locked"] is True, runner
assert runner["run_untagged"] is False, runner
assert runner["tag_list"] == ["ci-internal"], runner
projects = [item["path_with_namespace"] for item in runner["projects"]]
assert projects == ["__GITLAB_PROJECT__"], projects
print("pass: ci-internal runner configuration")'
```

`gitlab-runner verify` 应输出 `is valid`。随后删除本地 token 文件，并用 pipeline API
确认 main pipeline 从 `pending` 进入 `running`，最终为 `success`：

```bash
rm -f /tmp/__PROJECT_NAME__-runner.json
tools/gitlab-api.sh project GET 'pipelines/<pipeline_id>'
```
