#!/usr/bin/env bash
# One-command Hetzner benchmark session: provision a single SUT+loadgen pair,
# run two sequential sweeps of the publishable subset, fetch results, print
# the session cost, destroy everything. "Rent it and re-run" for readers.
#
# Usage:
#   scripts/hetzner/bench-run.sh [--plan] [--keep] [--yes] [--single-sweep]
#
#   --plan          Print every action without calling the hcloud API.
#   --keep          Skip destruction (debugging); instances keep billing!
#   --yes           No confirmation prompt before destruction.
#   --single-sweep  One sweep only (default is two sequential sweeps, whose
#                   bench-delta report is the run-to-run variance baseline).
#
# Requires: hcloud CLI authenticated (HCLOUD_TOKEN or active context),
# ssh, rsync. Everything this script creates carries the campaign label and
# destruction is scoped to exactly that label.

set -euo pipefail

# ── Config — single source for every name, type, and label ─────────────────
CAMPAIGN_LABEL="velocitybench=2026-07"
LOCATION="fsn1"
IMAGE="ubuntu-24.04"

SUT_NAME="vb-sut"
SUT_TYPE="ccx33"          # 8 vCPU / 32 GB dedicated — the machine readers rent
LOADGEN_NAME="vb-loadgen"
LOADGEN_TYPE="ccx23"      # 4 vCPU / 16 GB dedicated — k6 must not see steal

NETWORK_NAME="vb-net"
NETWORK_RANGE="10.7.0.0/24"
FIREWALL_NAME="vb-ssh-only"     # public ingress: SSH only; sweep runs on the private net
SSH_KEY_NAME="vb-bench-2026-07"
SSH_KEY_FILE="${HOME}/.ssh/vb_hetzner_2026_07"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRICES_FILE="${REPO_ROOT}/costs/instance-prices-2026-07.yaml"
REMOTE_DIR="/root/velocitybench"

# The publishable subset — keep in sync with
# .phases/2026-07-publishable-benchmark/phase-04-local-smoke.md
FRAMEWORKS="fraiseql-tv fraiseql-tv-cache fraiseql-v-nocache fraiseql-v-cache \
fraiseql-tv-audit hasura postgraphile actix-web-rest async-graphql mercurius \
apollo-server strawberry"
SWEEP_ARGS="--duration 30 --warmup 10 --cooldown 5 --tview-mode logged"

# ── Flags ───────────────────────────────────────────────────────────────────
PLAN=0 KEEP=0 YES=0 SWEEPS=2
for arg in "$@"; do
    case "$arg" in
        --plan) PLAN=1 ;;
        --keep) KEEP=1 ;;
        --yes) YES=1 ;;
        --single-sweep) SWEEPS=1 ;;
        *) echo "unknown flag: $arg" >&2; exit 2 ;;
    esac
done

# ── Helpers ─────────────────────────────────────────────────────────────────
say() { printf '%s\n' "$*"; }

run() {
    # Every side-effecting command goes through here: --plan prints, live runs.
    if (( PLAN )); then
        say "PLAN: $*"
    else
        say "+ $*"
        "$@"
    fi
}

price_hour() {
    # Read price_hour for an instance type from the campaign prices YAML —
    # the single source the report's cost composite uses too.
    awk -v inst="$1" '
        $1 == inst":" { in_inst = 1; next }
        in_inst && $1 == "price_hour:" { print $2; exit }
        in_inst && /^[^ ]/ { in_inst = 0 }
    ' "$PRICES_FILE"
}

SUT_PRICE="$(price_hour "$SUT_TYPE")"
LOADGEN_PRICE="$(price_hour "$LOADGEN_TYPE")"
PAIR_PRICE="$(awk -v a="$SUT_PRICE" -v b="$LOADGEN_PRICE" 'BEGIN{printf "%.4f", a+b}')"

ssh_sut()     { run ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new "root@${SUT_IP:-<sut-public-ip>}" "$@"; }
ssh_loadgen() { run ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new "root@${LOADGEN_IP:-<loadgen-public-ip>}" "$@"; }

START_EPOCH="$(date +%s)"

cost_note() {
    local end_epoch hours cost
    end_epoch="$(date +%s)"
    hours="$(awk -v s="$START_EPOCH" -v e="$end_epoch" 'BEGIN{printf "%.2f", (e-s)/3600}')"
    cost="$(awk -v h="$hours" -v p="$PAIR_PRICE" 'BEGIN{printf "%.2f", h*p}')"
    say ""
    say "── Session cost ─────────────────────────────────────────────"
    say "  ${SUT_TYPE} (SUT)      €${SUT_PRICE}/h"
    say "  ${LOADGEN_TYPE} (loadgen)  €${LOADGEN_PRICE}/h"
    say "  pair               €${PAIR_PRICE}/h × ${hours}h ≈ €${cost}"
    say "  (billing granularity is hourly; actual invoice may round up)"
}

destroy_all() {
    say ""
    say "── Destroy (scoped to label ${CAMPAIGN_LABEL}) ──────────────"
    if (( KEEP )); then
        say "--keep set: SKIPPING destruction — instances keep billing until you run:"
        say "  hcloud server list -l ${CAMPAIGN_LABEL}"
        say "  scripts/hetzner/bench-run.sh --yes   # or delete manually"
        return 0
    fi
    if (( ! YES && ! PLAN )); then
        read -r -p "Delete ALL resources labeled ${CAMPAIGN_LABEL}? [y/N] " reply
        [[ "$reply" == [yY]* ]] || { say "aborted — nothing destroyed"; return 1; }
    fi
    # Delete only what carries the campaign label — never anything else.
    run hcloud server delete -l "$CAMPAIGN_LABEL"
    run hcloud firewall delete "$FIREWALL_NAME"
    run hcloud network delete "$NETWORK_NAME"
    run hcloud ssh-key delete "$SSH_KEY_NAME"
    if (( ! PLAN )); then
        say "verify: hcloud server list -l ${CAMPAIGN_LABEL}   # must be empty"
    fi
}

# ── Preflight ───────────────────────────────────────────────────────────────
say "VelocityBench Hetzner session — SUT ${SUT_TYPE} + loadgen ${LOADGEN_TYPE}"
say "Campaign label: ${CAMPAIGN_LABEL}   location: ${LOCATION}   image: ${IMAGE}"
say "Prices (${PRICES_FILE##*/}): ${SUT_TYPE}=€${SUT_PRICE}/h ${LOADGEN_TYPE}=€${LOADGEN_PRICE}/h pair=€${PAIR_PRICE}/h"
say "Sweeps: ${SWEEPS} (sequential, same box) — frameworks: ${FRAMEWORKS}"
say ""

if (( ! PLAN )); then
    command -v hcloud >/dev/null || { echo "hcloud CLI not found" >&2; exit 1; }
    command -v rsync >/dev/null || { echo "rsync not found" >&2; exit 1; }
    hcloud server list >/dev/null || { echo "hcloud not authenticated (set HCLOUD_TOKEN or context)" >&2; exit 1; }
    [[ -f "$SSH_KEY_FILE" ]] || run ssh-keygen -t ed25519 -N "" -f "$SSH_KEY_FILE"
fi

# ── 1. Create network, firewall, SSH key, instances ────────────────────────
say "── 1. Provision network + instances ─────────────────────────"
run hcloud network create --name "$NETWORK_NAME" --ip-range "$NETWORK_RANGE" --label "$CAMPAIGN_LABEL"
run hcloud network add-subnet "$NETWORK_NAME" --network-zone eu-central --type cloud --ip-range "$NETWORK_RANGE"
run hcloud firewall create --name "$FIREWALL_NAME" --label "$CAMPAIGN_LABEL" \
    --rules-file "${REPO_ROOT}/scripts/hetzner/firewall-ssh-only.json"
run hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key-from-file "${SSH_KEY_FILE}.pub" --label "$CAMPAIGN_LABEL"

for spec in "${SUT_NAME}:${SUT_TYPE}" "${LOADGEN_NAME}:${LOADGEN_TYPE}"; do
    name="${spec%%:*}" type="${spec##*:}"
    run hcloud server create --name "$name" --type "$type" --image "$IMAGE" \
        --location "$LOCATION" --network "$NETWORK_NAME" \
        --firewall "$FIREWALL_NAME" --ssh-key "$SSH_KEY_NAME" \
        --label "$CAMPAIGN_LABEL" \
        --user-data-from-file "${REPO_ROOT}/scripts/hetzner/cloud-init.yaml"
done

if (( PLAN )); then
    SUT_IP="<sut-public-ip>" LOADGEN_IP="<loadgen-public-ip>"
    SUT_PRIVATE_IP="<sut-private-ip>"
else
    SUT_IP="$(hcloud server ip "$SUT_NAME")"
    LOADGEN_IP="$(hcloud server ip "$LOADGEN_NAME")"
    SUT_PRIVATE_IP="$(hcloud server describe "$SUT_NAME" -o 'format={{(index .PrivateNet 0).IP}}')"
    say "SUT ${SUT_IP} (private ${SUT_PRIVATE_IP}) — loadgen ${LOADGEN_IP}"
    say "waiting for cloud-init (docker install) on both instances..."
    for ip in "$SUT_IP" "$LOADGEN_IP"; do
        until ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
              "root@${ip}" cloud-init status --wait >/dev/null 2>&1; do sleep 10; done
    done
fi

# ── 2. Sync repo + seed database on the SUT ─────────────────────────────────
say ""
say "── 2. rsync repo + seed DB ──────────────────────────────────"
for ip_desc in "SUT:${SUT_IP}" "loadgen:${LOADGEN_IP}"; do
    ip="${ip_desc##*:}"
    run rsync -az --delete \
        --exclude .git --exclude '.venv' --exclude venv --exclude node_modules \
        --exclude reports --exclude '.phases*' \
        -e "ssh -i ${SSH_KEY_FILE} -o StrictHostKeyChecking=accept-new" \
        "${REPO_ROOT}/" "root@${ip}:${REMOTE_DIR}/"
done
# SUT: postgres up + seeded (logged tviews — the publishable profile)
ssh_sut "cd ${REMOTE_DIR} && TVIEW_PERSISTENCE=logged docker compose up -d postgres && docker compose logs --tail 5 postgres"
# loadgen: k6 + python only — the SUT stays dumb (Docker + repo)
ssh_loadgen "command -v k6 >/dev/null || (gpg -k >/dev/null; curl -fsSL https://dl.k6.io/key.gpg | gpg --dearmor -o /usr/share/keyrings/k6.gpg && echo 'deb [signed-by=/usr/share/keyrings/k6.gpg] https://dl.k6.io/deb stable main' > /etc/apt/sources.list.d/k6.list && apt-get update -qq && apt-get install -y -qq k6)"

# ── 3. Headroom re-check from loadgen against SUT private IP ───────────────
say ""
say "── 3. Loadgen headroom re-check (null target on SUT) ────────"
ssh_loadgen "cd ${REMOTE_DIR} && DOCKER_HOST=ssh://root@${SUT_PRIVATE_IP} \
python3 tests/benchmark/loadgen_headroom.py --host ${SUT_PRIVATE_IP} --min-rps 30000"

# ── 4. Sweeps (sequential, same box) ────────────────────────────────────────
# Results are collected even if a sweep dies mid-run — the hours are paid for.
trap 'collect_results || true; cost_note' EXIT

collect_results() {
    say ""
    say "── 5. rsync results back ────────────────────────────────────"
    run rsync -az -e "ssh -i ${SSH_KEY_FILE} -o StrictHostKeyChecking=accept-new" \
        "root@${LOADGEN_IP:-<loadgen-public-ip>}:${REMOTE_DIR}/reports/" "${REPO_ROOT}/reports/hetzner-2026-07/"
}

for n in $(seq 1 "$SWEEPS"); do
    say ""
    say "── 4.${n} Sweep ${n}/${SWEEPS} ──────────────────────────────────────"
    # Orchestration runs on the loadgen; DOCKER_HOST points every docker/compose
    # call (framework start/stop, RSS sampling, cold-start restarts) at the SUT.
    ssh_loadgen "cd ${REMOTE_DIR} && DOCKER_HOST=ssh://root@${SUT_PRIVATE_IP} \
python3 tests/benchmark/bench_sequential.py \
--target-host ${SUT_PRIVATE_IP} --frameworks ${FRAMEWORKS} ${SWEEP_ARGS} \
--output ${REMOTE_DIR}/reports/bench-hetzner-\$(date +%F)-sweep${n}.md"
done

collect_results
trap 'cost_note' EXIT

if (( SWEEPS >= 2 )); then
    say ""
    say "── 4.9 Variance baseline: bench-delta sweep 1 vs sweep 2 ────"
    # Non-fatal: the baseline documents the variance; gating happens in Phase 06.
    run bash -c "cd ${REPO_ROOT} && python3 scripts/bench-delta.py \
reports/hetzner-2026-07/bench-hetzner-\$(date +%F)-sweep1.json \
reports/hetzner-2026-07/bench-hetzner-\$(date +%F)-sweep2.json \
--output reports/hetzner-2026-07/variance-baseline-\$(date +%F).md" || true
fi

# ── 6. Destroy ──────────────────────────────────────────────────────────────
destroy_all
cost_note
trap - EXIT
