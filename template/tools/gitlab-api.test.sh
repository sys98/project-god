#!/usr/bin/env bash
set -euo pipefail

if [[ "${GITLAB_API_TEST_FAKE_CURL:-}" == "1" ]]; then
  printf '%s\n' "$@"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="$({
  GITLAB_API_TEST_FAKE_CURL=1 \
    GITLAB_API_BASE=https://gitlab.example/api/v4 \
    GITLAB_CURL_BIN="$SCRIPT_DIR/gitlab-api.test.sh" \
    GITLAB_PROJECT_ID=13 \
    GITLAB_TOKEN=test-token \
    "$SCRIPT_DIR/gitlab-api.sh" create-project-runner
})"

assert_arg() {
  local expected="$1"
  if ! grep -Fqx -- "$expected" <<<"$OUTPUT"; then
    printf 'FAIL: missing curl argument: %s\n' "$expected" >&2
    exit 1
  fi
}

assert_arg "POST"
assert_arg "runner_type=project_type"
assert_arg "project_id=13"
assert_arg "description=__PROJECT_NAME__-ci"
assert_arg "tag_list=ci-internal"
assert_arg "locked=true"
assert_arg "run_untagged=false"
assert_arg "access_level=not_protected"
assert_arg "https://gitlab.example/api/v4/user/runners"

if grep -Eq '(staging|production)-internal' <<<"$OUTPUT"; then
  printf 'FAIL: skeleton CI must not create staging-internal or production-internal runners\n' >&2
  exit 1
fi

if GITLAB_API_TEST_FAKE_CURL=1 \
  GITLAB_API_BASE=https://gitlab.example/api/v4 \
  GITLAB_CURL_BIN="$SCRIPT_DIR/gitlab-api.test.sh" \
  GITLAB_PROJECT_ID=13 \
  GITLAB_TOKEN=test-token \
  "$SCRIPT_DIR/gitlab-api.sh" create-project-runner \
    __PROJECT_NAME__-production-internal production-internal ref_protected \
    >/dev/null 2>&1; then
  printf 'FAIL: create-project-runner must reject non-ci runner arguments\n' >&2
  exit 1
fi

printf 'PASS: create-project-runner is fixed to the ci-internal project runner\n'
