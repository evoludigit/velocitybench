#!/usr/bin/env bash
# One-command Hetzner benchmark session: provision a single SUT+loadgen pair,
# run two sequential sweeps of the publishable subset, fetch results, print
# the session cost, destroy everything. "Rent it and re-run" for readers.
#
# Usage:
#   scripts/hetzner/bench-run.sh [--plan] [--keep] [--yes] [--single-sweep] [--sweeps=N]
#
#   --plan          Print every action without calling the hcloud API.
#   --keep          Skip destruction (debugging); instances keep billing!
#   --yes           No confirmation prompt before destruction.
#   --single-sweep  One sweep only (default is two sequential sweeps, whose
#                   bench-delta report is the run-to-run variance baseline).
#   --sweeps=N      Run N sequential sweeps (Phase 06 publishable = 4: a
#                   throwaway warm-up on the fresh seed, discarded, then three
#                   warm sweeps whose per-cell median is the published number).
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
# ccx23 was the plan, but the project's dedicated-core quota (8) is fully
# consumed by the SUT and cpx31/cx32 are unorderable in fsn1. cpx42 gives k6
# 8 shared vCPUs; the pre-sweep headroom gate proves it is not the bottleneck.
LOADGEN_TYPE="cpx42"

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
        --sweeps=*) SWEEPS="${arg#*=}" ;;
        *) echo "unknown flag: $arg" >&2; exit 2 ;;
    esac
done
[[ "$SWEEPS" =~ ^[1-9][0-9]*$ ]] || { echo "--sweeps must be a positive integer (got: $SWEEPS)" >&2; exit 2; }

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

ssh_sut()     { run ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes "root@${SUT_IP:-<sut-public-ip>}" "$@"; }
ssh_loadgen() { run ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes "root@${LOADGEN_IP:-<loadgen-public-ip>}" "$@"; }

START_EPOCH="$(date +%s)"
# Fixed once per session: sweep filenames must not drift across midnight
# (sweep 1 launched at 23:5x and sweep 2 at 00:0x would otherwise disagree
# with the delta step's date computation).
SESSION_DATE="$(date +%F)"

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
    # Delete only what this script created — exact names, verified against the
    # campaign label first (hcloud server delete has no label selector).
    if (( ! PLAN )); then
        for name in "$SUT_NAME" "$LOADGEN_NAME"; do
            if hcloud server describe "$name" -o 'format={{.Labels}}' 2>/dev/null | grep -q "velocitybench"; then
                run hcloud server delete "$name"
            fi
        done
    else
        run hcloud server delete "$SUT_NAME"    # label-verified at runtime
        run hcloud server delete "$LOADGEN_NAME"
    fi
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

# ── 1. Create network, firewall, SSH key, instances (idempotent) ───────────
say "── 1. Provision network + instances ─────────────────────────"
exists() { (( PLAN )) && return 1; hcloud "$1" describe "$2" >/dev/null 2>&1; }

exists network "$NETWORK_NAME" || {
    run hcloud network create --name "$NETWORK_NAME" --ip-range "$NETWORK_RANGE" --label "$CAMPAIGN_LABEL"
    run hcloud network add-subnet "$NETWORK_NAME" --network-zone eu-central --type cloud --ip-range "$NETWORK_RANGE"
}
exists firewall "$FIREWALL_NAME" || run hcloud firewall create --name "$FIREWALL_NAME" \
    --label "$CAMPAIGN_LABEL" --rules-file "${REPO_ROOT}/scripts/hetzner/firewall-ssh-only.json"
exists ssh-key "$SSH_KEY_NAME" || run hcloud ssh-key create --name "$SSH_KEY_NAME" \
    --public-key-from-file "${SSH_KEY_FILE}.pub" --label "$CAMPAIGN_LABEL"

for spec in "${SUT_NAME}:${SUT_TYPE}" "${LOADGEN_NAME}:${LOADGEN_TYPE}"; do
    name="${spec%%:*}" type="${spec##*:}"
    exists server "$name" || run hcloud server create --name "$name" --type "$type" --image "$IMAGE" \
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
        until ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes -o ConnectTimeout=5 \
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
        --exclude tests/perf --exclude target --exclude '.gradle' \
        --exclude __pycache__ --exclude '*.pyc' --exclude '.pytest_cache' \
        --exclude '.ruff_cache' --exclude costs/test_venv \
        -e "ssh -i ${SSH_KEY_FILE} -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes" \
        "${REPO_ROOT}/" "root@${ip}:${REMOTE_DIR}/"
done
# loadgen → SUT ssh identity: DOCKER_HOST=ssh://root@SUT needs a key on the
# loadgen. The campaign key only opens these two instances and dies with them.
run rsync -az -e "ssh -i ${SSH_KEY_FILE} -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes" \
    "$SSH_KEY_FILE" "root@${LOADGEN_IP}:/root/.ssh/id_ed25519"
ssh_loadgen "chmod 600 /root/.ssh/id_ed25519 && printf 'Host ${NETWORK_RANGE%%.0/*}.*\n  User root\n  StrictHostKeyChecking accept-new\n  ControlMaster auto\n  ControlPath /root/.ssh/cm-%%r@%%h\n  ControlPersist 10m\n' > /root/.ssh/config"
# SUT: postgres up + seeded (logged tviews — the publishable profile).
# The compose file declares the docker network as external — create it first.
# First boot seeds 10k users / 500k comments + tv build — wait for it.
ssh_sut "docker network inspect velocitybench-benchmark >/dev/null 2>&1 || docker network create velocitybench-benchmark"
ssh_sut "cd ${REMOTE_DIR} && TVIEW_PERSISTENCE=logged docker compose up -d postgres"
# -h 127.0.0.1 forces TCP: during docker-entrypoint init postgres only serves
# the unix socket, so a socket check releases while the 500k-comment seed and
# tview build are still running. Full readiness = TCP up + tv_comment complete.
ssh_sut "cd ${REMOTE_DIR} && for i in \$(seq 1 360); do \
docker compose exec -T postgres psql -h 127.0.0.1 -U benchmark -d velocitybench_benchmark -tAc \
'SELECT count(*) FROM benchmark.tv_comment' 2>/dev/null | grep -qx 500005 && exit 0; sleep 10; done; \
echo 'DB seed did not complete within 60 min' >&2; exit 1"
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
    run rsync -az -e "ssh -i ${SSH_KEY_FILE} -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes" \
        "root@${LOADGEN_IP:-<loadgen-public-ip>}:${REMOTE_DIR}/reports/" "${REPO_ROOT}/reports/hetzner-2026-07/"
}

for n in $(seq 1 "$SWEEPS"); do
    say ""
    say "── 4.${n} Sweep ${n}/${SWEEPS} ──────────────────────────────────────"
    # Orchestration runs on the loadgen; DOCKER_HOST points every docker/compose
    # call (framework start/stop, RSS sampling, cold-start restarts) at the SUT.
    # Detached (nohup + pidfile) so a dropped operator connection cannot kill a
    # paid multi-hour sweep; we poll the pid and tail the log for liveness.
    # Braces keep the & scoped to nohup: without them the WHOLE cd&&mkdir&&nohup
    # chain backgrounds and echo \$! races ahead of mkdir (first live run bug).
    ssh_loadgen "cd ${REMOTE_DIR} && mkdir -p reports && { \
nohup env DOCKER_HOST=ssh://root@${SUT_PRIVATE_IP} \
python3 tests/benchmark/bench_sequential.py \
--target-host ${SUT_PRIVATE_IP} --frameworks ${FRAMEWORKS} ${SWEEP_ARGS} \
--output ${REMOTE_DIR}/reports/bench-hetzner-${SESSION_DATE}-sweep${n}.md \
> ${REMOTE_DIR}/reports/sweep${n}.log 2>&1 < /dev/null & \
echo \$! > ${REMOTE_DIR}/reports/sweep${n}.pid; }"
    if (( ! PLAN )); then
        sleep 20
        while ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes "root@${LOADGEN_IP}" \
              "kill -0 \$(cat ${REMOTE_DIR}/reports/sweep${n}.pid) 2>/dev/null"; do
            ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes "root@${LOADGEN_IP}" \
                "tail -1 ${REMOTE_DIR}/reports/sweep${n}.log" 2>/dev/null || true
            sleep 60
        done
        if ! ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes "root@${LOADGEN_IP}" \
             "grep -q 'Report written to' ${REMOTE_DIR}/reports/sweep${n}.log"; then
            say "sweep ${n} FAILED — last log lines:"
            ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes "root@${LOADGEN_IP}" \
                "tail -30 ${REMOTE_DIR}/reports/sweep${n}.log" || true
            exit 1
        fi
        say "sweep ${n} complete ✓"
    fi
done

collect_results
trap 'cost_note' EXIT

if (( SWEEPS >= 2 )); then
    # Compare the last two sweeps — both warm (sweep 1 on a fresh seed is the
    # discarded warm-up), so this baseline reflects warm-to-warm variance.
    prev=$(( SWEEPS - 1 ))
    say ""
    say "── 4.9 Variance baseline: bench-delta sweep ${prev} vs sweep ${SWEEPS} ────"
    # Non-fatal: the baseline documents the variance; gating happens in Phase 06.
    run bash -c "cd ${REPO_ROOT} && python3 scripts/bench-delta.py \
reports/hetzner-2026-07/bench-hetzner-${SESSION_DATE}-sweep${prev}.json \
reports/hetzner-2026-07/bench-hetzner-${SESSION_DATE}-sweep${SWEEPS}.json \
--output reports/hetzner-2026-07/variance-baseline-${SESSION_DATE}.md" || true
fi

# ── 6. Destroy ──────────────────────────────────────────────────────────────
destroy_all
cost_note
trap - EXIT
