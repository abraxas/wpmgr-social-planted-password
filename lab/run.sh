#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-wpmgrh04}"
export PYTHONUNBUFFERED=1

LABEL="WPMGR-H04-SOCIAL-PLANT"
WITNESS="WPMGR-H04-PLANTED-PASSWORD-SURVIVES"
PIN_COMMIT="e1b3a163988c9f1c31bc93922ea34322fa188792"
REPO_URL="${WPMGR_SRC_URL:-https://github.com/mosamlife/wpmgr.git}"
PIN_SRC="$(pwd)/src"
IMAGE_API="wpmgr-lab:v0.61.199"
IMAGE_WEB="wpmgr-lab-web:v0.61.199"

port_free() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
      return 1
    fi
    return 0
  fi
  python3 - "${port}" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("127.0.0.1", port))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
}

pick_ports() {
  local base=18180
  if port_free 18180 && port_free 18181 && port_free 18182 && port_free 18183 \
     && port_free 18184 && port_free 18185 && port_free 18186; then
    WEB_PORT=18180
    API_PORT=18181
    PG_PORT=18182
    REDIS_PORT=18183
    DEX_PORT=18184
    MAILPIT_PORT=18185
    MAILPIT_SMTP_PORT=18186
    return 0
  fi
  local n
  for n in $(seq 18300 2 18314); do
    if port_free "${n}" && port_free $((n+1)) && port_free $((n+2)) \
       && port_free $((n+3)) && port_free $((n+4)) && port_free $((n+5)) \
       && port_free $((n+6)); then
      WEB_PORT="${n}"
      API_PORT=$((n+1))
      PG_PORT=$((n+2))
      REDIS_PORT=$((n+3))
      DEX_PORT=$((n+4))
      MAILPIT_PORT=$((n+5))
      MAILPIT_SMTP_PORT=$((n+6))
      return 0
    fi
  done
  return 1
}

render_dex() {
  sed -e "s/__DEX_PORT__/${DEX_PORT}/g" -e "s/__WEB_PORT__/${WEB_PORT}/g" \
    dex/config.yaml.tmpl > dex/config.yaml
}

down() {
  docker compose -p "${COMPOSE_PROJECT_NAME}" down -v --remove-orphans >/dev/null 2>&1 || true
}

fail_setup() {
  local reason="$1"
  echo "FAIL ${LABEL} ${reason} ${WITNESS}" | tee poc-last-run.txt
  down
  exit 1
}

ensure_images() {
  if docker image inspect "${IMAGE_API}" >/dev/null 2>&1 \
     && docker image inspect "${IMAGE_WEB}" >/dev/null 2>&1; then
    echo "IOC reuse ${IMAGE_API} ${IMAGE_WEB}"
    return 0
  fi
  echo "== flock build lab images =="
  # macOS has no flock(1); fcntl lock on the same path serialises sibling labs.
  PIN_SRC="${PIN_SRC}" IMAGE_API="${IMAGE_API}" IMAGE_WEB="${IMAGE_WEB}" python3 - <<'PY'
import fcntl
import os
import subprocess
import sys

pin = os.environ["PIN_SRC"]
api = os.environ["IMAGE_API"]
web = os.environ["IMAGE_WEB"]
fd = os.open("/tmp/wpmgr-lab-image.lock", os.O_CREAT | os.O_RDWR, 0o644)
fcntl.flock(fd, fcntl.LOCK_EX)

def have(tag: str) -> bool:
    return subprocess.run(
        ["docker", "image", "inspect", tag],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0

try:
    if not have(api):
        subprocess.check_call(
            [
                "docker", "build", "-t", api,
                "--build-arg", "VERSION=0.61.199",
                "-f", f"{pin}/infra/Dockerfile.api", pin,
            ]
        )
    if not have(web):
        subprocess.check_call(
            [
                "docker", "build", "-t", web,
                "--build-arg", "BUILD_VERSION=0.61.199",
                "-f", f"{pin}/infra/Dockerfile.web", pin,
            ]
        )
finally:
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)
PY
}

trap down EXIT
chmod +x poc.py postgres-init/01-app-role.sh

ensure_pin() {
  if [[ ! -e "${PIN_SRC}/.git" ]]; then
    git clone --filter=blob:none --no-checkout "${REPO_URL}" "${PIN_SRC}" || fail_setup "clone-failed"
    git -C "${PIN_SRC}" fetch --depth 1 origin "${PIN_COMMIT}" || fail_setup "fetch-failed"
    git -C "${PIN_SRC}" checkout --detach FETCH_HEAD || fail_setup "checkout-failed"
  fi
  local got
  got="$(git -C "${PIN_SRC}" rev-parse HEAD)"
  if [[ "${got}" != "${PIN_COMMIT}" ]]; then
    fail_setup "pin-mismatch"
  fi
}

ensure_pin

if ! pick_ports; then
  fail_setup "no-free-loopback-ports"
fi
export WEB_PORT API_PORT PG_PORT REDIS_PORT DEX_PORT MAILPIT_PORT MAILPIT_SMTP_PORT
echo "IOC ports web=${WEB_PORT} api=${API_PORT} pg=${PG_PORT} redis=${REDIS_PORT} dex=${DEX_PORT} mailpit=${MAILPIT_PORT} smtp=${MAILPIT_SMTP_PORT}"

render_dex
down
ensure_images

echo "== docker compose up =="
up_ok=0
attempt=1
while [[ "${attempt}" -le 8 ]]; do
  if docker compose -p "${COMPOSE_PROJECT_NAME}" up -d; then
    up_ok=1
    break
  fi
  echo "IOC compose-up-retry attempt=${attempt}"
  down
  sleep 20
  attempt=$((attempt + 1))
done
if [[ "${up_ok}" != 1 ]]; then
  fail_setup "compose-up-failed"
fi

API_URL="http://127.0.0.1:${API_PORT}"
echo "== wait ${API_URL}/healthz =="
ready=0
for i in $(seq 1 90); do
  code="$(curl -sS -o /tmp/wpmgr-h04-health.txt -w '%{http_code}' --max-time 5 \
    "${API_URL}/healthz" || true)"
  if [[ "${code}" == "200" ]]; then
    ready=1
    echo "IOC api-ready attempt=${i} http=${code}"
    break
  fi
  echo "IOC api-wait attempt=${i} http=${code}"
  sleep 4
done
if [[ "${ready}" != 1 ]]; then
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --no-color --tail=80 api || true
  fail_setup "api-not-ready"
fi

web_code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 \
  "http://127.0.0.1:${WEB_PORT}/" || true)"
echo "IOC web-http=${web_code}"

echo "== poc.py =="
set +e
python3 ./poc.py | tee poc-last-run.txt
rc=${PIPESTATUS[0]}
set -e

if [[ "${rc}" -ne 0 ]]; then
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --no-color --tail=120 api > api-tail.log || true
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --no-color --tail=40 dex > dex-tail.log || true
fi

if [[ ! -f poc-last-run.txt ]] || ! tail -n 1 poc-last-run.txt | grep -qE '^(SUCCESS|FAIL) '; then
  echo "FAIL ${LABEL} poc-exit-${rc} ${WITNESS}" >> poc-last-run.txt
  rc=1
fi

exit "${rc}"
