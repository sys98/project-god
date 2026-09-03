#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------
# [L3][COORD] repo://tools/gitlab-api.sh
# [INPUT]  macOS keychain（钥匙串）记录 JUNBO_GITLAB_API_TOKEN、或 GITLAB_TOKEN/GITLAB_PRIVATE_TOKEN。
# [OUTPUT] 统一 GitLab REST API（接口）调用入口；封装 project/issue/runner API，默认不打印输入 token。
# [POS]    Agent/GitLab 自动化脚本包；封装 repo://docs/agents/gitlab-api-operations.md 的凭证和 endpoint 陷阱。
# [PROTOCOL] 变更时更新此头部，然后检查 repo://tools/AGENTS.md 与 repo://docs/agents/gitlab-api-operations.md
# ---------------------------------------------------------------------
# [L5] 环境变量
# GITLAB_TOKEN / GITLAB_PRIVATE_TOKEN  token 直给，前者优先。[FAIL] 两者缺失时回退 keychain。
# GITLAB_API_BASE                API base。默认 https://192.168.121.43/api/v4。
# GITLAB_PROJECT_PATH_ENCODED    URL-encoded 项目路径。默认 __GITLAB_PROJECT_ENCODED__。
# GITLAB_PROJECT_ID              数字项目 ID。[PAIR] create-project-runner 要求数字 ID；缺失时从项目 API 读回（见 [L4] project_id）。
# GITLAB_KEYCHAIN_SERVICE        keychain 服务名。默认 JUNBO_GITLAB_API_TOKEN。
# GITLAB_KEYCHAIN_ACCOUNT        指定 keychain account。缺省时按 GITLAB_KEYCHAIN_ACCOUNTS 回退列表逐个试。
# GITLAB_KEYCHAIN_ACCOUNTS       account 回退列表。默认 "dimon simon"。
# GITLAB_CURL_BIN / GITLAB_SECURITY_BIN  外部命令路径覆写。默认 curl / security。
# ---------------------------------------------------------------------

API_BASE="${GITLAB_API_BASE:-https://192.168.121.43/api/v4}"
PROJECT_PATH_ENCODED="${GITLAB_PROJECT_PATH_ENCODED:-__GITLAB_PROJECT_ENCODED__}"
KEYCHAIN_ACCOUNT="${GITLAB_KEYCHAIN_ACCOUNT:-}"
KEYCHAIN_ACCOUNT_FALLBACKS="${GITLAB_KEYCHAIN_ACCOUNTS:-dimon simon}"
KEYCHAIN_SERVICE="${GITLAB_KEYCHAIN_SERVICE:-JUNBO_GITLAB_API_TOKEN}"
CURL_BIN="${GITLAB_CURL_BIN:-curl}"
SECURITY_BIN="${GITLAB_SECURITY_BIN:-security}"

usage() {
  cat >&2 <<'EOF'
Usage:
  tools/gitlab-api.sh token-check
  tools/gitlab-api.sh project METHOD PATH [curl args...]
  tools/gitlab-api.sh raw METHOD PATH [curl args...]
  tools/gitlab-api.sh issue IID
  tools/gitlab-api.sh mr IID
  tools/gitlab-api.sh project-runners
  tools/gitlab-api.sh runners-all
  tools/gitlab-api.sh create-project-runner

Examples:
  tools/gitlab-api.sh project GET ''
  tools/gitlab-api.sh project GET 'issues/182'
  tools/gitlab-api.sh project GET 'pipelines?ref=main'
  tools/gitlab-api.sh raw GET 'version'
  umask 077 && tools/gitlab-api.sh create-project-runner > /tmp/__PROJECT_NAME__-runner.json
EOF
}

# ---------------------------------------------------------------------
# [L4] gitlab_token
# [OUT]       stdout 仅输出 token 本体。
# [INVARIANT] 解析顺序：GITLAB_TOKEN > GITLAB_PRIVATE_TOKEN > keychain（指定 account，否则按回退列表）。token 永不写入日志与错误输出。
# [FAIL]      全部来源缺失时 stderr 给出 keychain 录入命令（恢复动作），exit 2。
# [TEST]      无行为级自动化，Unknown；CI hygiene 仅做 bash -n。
# ---------------------------------------------------------------------
gitlab_token() {
  if [[ -n "${GITLAB_TOKEN:-}" ]]; then
    printf '%s' "$GITLAB_TOKEN"
    return
  fi
  if [[ -n "${GITLAB_PRIVATE_TOKEN:-}" ]]; then
    printf '%s' "$GITLAB_PRIVATE_TOKEN"
    return
  fi
  if command -v "$SECURITY_BIN" >/dev/null 2>&1; then
    if [[ -n "$KEYCHAIN_ACCOUNT" ]]; then
      if "$SECURITY_BIN" find-generic-password -a "$KEYCHAIN_ACCOUNT" -s "$KEYCHAIN_SERVICE" -w; then
        return
      fi
    else
      local account
      local token
      for account in $KEYCHAIN_ACCOUNT_FALLBACKS; do
        if token="$("$SECURITY_BIN" find-generic-password -a "$account" -s "$KEYCHAIN_SERVICE" -w 2>/dev/null)"; then
          printf '%s' "$token"
          return
        fi
      done
    fi
  fi
  cat >&2 <<EOF
ERROR: GitLab token not found.
Set GITLAB_TOKEN, or create macOS keychain item:
  security add-generic-password -a ${KEYCHAIN_ACCOUNT:-simon} -s $KEYCHAIN_SERVICE -w '<token>'
Default keychain account fallbacks: $KEYCHAIN_ACCOUNT_FALLBACKS
EOF
  exit 2
}

api_url() {
  local path="${1#/}"
  printf '%s/%s' "${API_BASE%/}" "$path"
}

project_path() {
  local path="${1#/}"
  if [[ -z "$path" ]]; then
    printf 'projects/%s' "$PROJECT_PATH_ENCODED"
  else
    printf 'projects/%s/%s' "$PROJECT_PATH_ENCODED" "$path"
  fi
}

# ---------------------------------------------------------------------
# [L4] project_id
# [OUT]       GitLab project numeric id（项目数字 ID），优先取 GITLAB_PROJECT_ID（显式环境变量），否则从项目 API 读回。
# [INVARIANT] POST /user/runners（创建 runner 配置）要求 project_id 是数字，不接受 URL-encoded path。
# [FAIL]      项目 API 响应没有 id 时 fail fast，避免创建 runner 时落到错误 scope。
# [TEST]      repo://tools/gitlab-api.test.sh
# ---------------------------------------------------------------------
project_id() {
  if [[ -n "${GITLAB_PROJECT_ID:-}" ]]; then
    printf '%s\n' "$GITLAB_PROJECT_ID"
    return
  fi
  api_call GET "$(project_path "")" | python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])'
}

# ---------------------------------------------------------------------
# [L4] api_call
# [IN]        METHOD、API path、透传的 curl 参数。[OUT] 响应 body 到 stdout。
# [INVARIANT] -k 关闭 TLS 校验：信任边界是内网 GitLab（默认 API_BASE 为内网 IP）；--fail-with-body 使 HTTP 4xx/5xx 非零退出且 body 已输出供排障。
# [FAIL]      curl 非零退出经 set -e 上抛，调用方不兜底。
# ---------------------------------------------------------------------
api_call() {
  local method="$1"
  local path="$2"
  shift 2
  local token
  token="$(gitlab_token)"
  "$CURL_BIN" -skS --fail-with-body \
    --request "$method" \
    --header "PRIVATE-TOKEN: $token" \
    "$@" \
    "$(api_url "$path")"
}

# ---------------------------------------------------------------------
# [L5] create-project-runner 固定配置
# description  __PROJECT_NAME__-ci；GitLab runner 展示名。
# tag_list     ci-internal；与 repo://.gitlab-ci.yml default.tags 配对。
# access_level not_protected；骨架期 CI 检查 main 与 MR。
# [INVARIANT] locked=true、run_untagged=false 固定，避免跨项目或无 tag job 误调度。
# [FAIL] 传入额外参数时 fail closed，避免提前创建 staging / production runner。
# [TEST] repo://tools/gitlab-api.test.sh
# ---------------------------------------------------------------------
main() {
  local command="${1:-}"
  case "$command" in
    token-check)
      api_call GET "user" >/dev/null
      printf 'ok: GitLab API token works for %s\n' "$API_BASE"
      ;;
    project)
      [[ $# -ge 3 ]] || { usage; exit 2; }
      api_call "$2" "$(project_path "$3")" "${@:4}"
      ;;
    raw)
      [[ $# -ge 3 ]] || { usage; exit 2; }
      api_call "$2" "$3" "${@:4}"
      ;;
    issue)
      [[ $# -eq 2 ]] || { usage; exit 2; }
      api_call GET "$(project_path "issues/$2")"
      ;;
    mr)
      [[ $# -eq 2 ]] || { usage; exit 2; }
      api_call GET "$(project_path "merge_requests/$2")"
      ;;
    project-runners)
      [[ $# -eq 1 ]] || { usage; exit 2; }
      api_call GET "$(project_path "runners?per_page=100")"
      ;;
    runners-all)
      [[ $# -eq 1 ]] || { usage; exit 2; }
      api_call GET "runners/all?per_page=100"
      ;;
    create-project-runner)
      [[ $# -eq 1 ]] || { usage; exit 2; }
      local numeric_project_id
      numeric_project_id="$(project_id)"
      api_call POST "user/runners" \
        --data "runner_type=project_type" \
        --data "project_id=$numeric_project_id" \
        --data-urlencode "description=__PROJECT_NAME__-ci" \
        --data "tag_list=ci-internal" \
        --data "locked=true" \
        --data "run_untagged=false" \
        --data "access_level=not_protected" \
        --data-urlencode "maintenance_note=Created by repo://tools/gitlab-api.sh for __PROJECT_NAME__ CI."
      ;;
    *)
      usage
      exit 2
      ;;
  esac
}

main "$@"
