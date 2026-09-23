#!/bin/sh
# One-way workstation -> Pi source sync, until GitHub credentials exist
# for a normal push/pull cycle (then this script retires).
#
# Usage: tools/sync_to_pi.sh [-n]   (-n = dry run)
#
# Deliberate choices, all protective:
# - ONE WAY only. Nothing is ever copied back; the Pi's ledger, .env
#   and live config never flow toward a dev machine.
# - NEVER touches .git/, so the Pi's checkout, history and the QoL
#   `git pull` path stay intact. No --delete either: files removed
#   upstream linger on the Pi until `git pull` reconciles them (it
#   shows them as expected, not as damage).
# - NEVER touches deployment secrets or state: .env*, state/, data/,
#   warehouse/, output/, logs/, *.db.
# - NEVER touches the live loop's config: config/paper_aggressive.yaml
#   is modified on the Pi on purpose (real cash figure). Sync every
#   other config; that one stays.
# - Skips machine-local debris: caches, editor/agent dirs, HAR/parquet
#   captures, build outputs (the Docker build regenerates web/dist
#   from source; node_modules likewise).
#
# After syncing, rebuild on the Pi (scoped to web so the paper loop is
# left running):
#   docker compose -f ~/workspace/volatility-ai/docker-compose.pi.yml build web
#   docker compose -f ~/workspace/volatility-ai/docker-compose.pi.yml up -d web
set -eu

PI_HOST="${PI_HOST:-ashitakalax@172.16.0.137}"
PI_DIR="${PI_DIR:-workspace/volatility-ai}"
DRY=""

if [ "${1:-}" = "-n" ]; then
  DRY="--dry-run"
  echo "DRY RUN -- nothing will transfer"
fi

REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
case "$REPO_ROOT" in
  *volatility-ai) ;;
  *)
    echo "refusing: $REPO_ROOT does not look like the volatility-ai checkout" >&2
    exit 1
    ;;
esac
for anchor in cli.py web/package.json docker-compose.pi.yml; do
  if [ ! -e "$REPO_ROOT/$anchor" ]; then
    echo "refusing: missing $anchor under $REPO_ROOT" >&2
    exit 1
  fi
done

# Smoke-test the link before moving bytes.
ssh -o BatchMode=yes -o ConnectTimeout=10 "$PI_HOST" "test -d $PI_DIR/.git" \
  || { echo "refusing: $PI_DIR/.git not reachable on $PI_HOST" >&2; exit 1; }

# shellcheck disable=SC2086
rsync -av $DRY \
  --exclude=.git/ \
  --exclude=.env --exclude=.env.fidelity --exclude=.env.staging --exclude=.env.production \
  --exclude=state/ --exclude=data/ --exclude=warehouse/ --exclude=output/ --exclude=logs/ \
  --exclude=node_modules/ --exclude=web/node_modules/ \
  --exclude=web/dist/ --exclude=web/bun.lock --exclude='web/*.tsbuildinfo' \
  --exclude=server.log --exclude='*.db' --exclude=ledger-*.db \
  --exclude=__pycache__/ --exclude=.venv/ \
  --exclude=.codegraph/ --exclude=.omo/ --exclude=.claude/ \
  --exclude=.remember/ --exclude=.pytest_cache/ --exclude=.ruff_cache/ \
  --exclude='*.har' --exclude='*.parquet' \
  --exclude=Implementation_ledger.md --exclude=x.parquet \
  --exclude=src/ \
  --exclude=config/paper_aggressive.yaml \
  "$REPO_ROOT/" "$PI_HOST:$PI_DIR/"

echo "synced to $PI_HOST:$PI_DIR (paper_aggressive.yaml, secrets and state untouched)"
