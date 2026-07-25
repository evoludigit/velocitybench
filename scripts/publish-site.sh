#!/usr/bin/env bash
# Build the VelocityBench site and publish it to the gh-pages branch, which
# GitHub Pages serves at https://evoludigit.github.io/velocitybench/.
#
# Usage:
#   scripts/publish-site.sh [run.json]
#
# run.json defaults to the published median-of-three. The build is Python
# stdlib only; the push happens in an isolated worktree so your working tree and
# current branch are never touched. Idempotent: a no-op if nothing changed.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="${1:-reports/hetzner-2026-07-22/bench-hetzner-2026-07-25-median.json}"
DIST="${ROOT}/site/dist"
BRANCH="gh-pages"
WT="$(mktemp -d)"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" 2>/dev/null || true; rm -rf "$WT"; }
trap cleanup EXIT

# 1. Build the self-contained site (index.html + data.json + llms.txt + run JSON).
"${PYTHON:-python3}" "${ROOT}/site/build.py" "$RUN" --out "$DIST"

# 2. Check gh-pages out into an isolated worktree (fresh orphan if it is new).
git -C "$ROOT" fetch origin "$BRANCH" 2>/dev/null || true
if git -C "$ROOT" show-ref --verify --quiet "refs/remotes/origin/${BRANCH}"; then
    git -C "$ROOT" worktree add -B "$BRANCH" "$WT" "origin/${BRANCH}"
else
    git -C "$ROOT" worktree add --orphan -b "$BRANCH" "$WT"
fi

# 3. Replace its contents with the fresh build; .nojekyll keeps Pages verbatim.
( cd "$WT" && git rm -rfq . 2>/dev/null || true )
cp "$DIST"/index.html "$DIST"/llms.txt "$WT/"
cp "$DIST"/*.json "$WT/"
touch "$WT/.nojekyll"

# 4. Commit + push (no-op if the build is byte-identical to what is live).
cd "$WT"
git add -A
if git diff --cached --quiet; then
    echo "publish-site: gh-pages already up to date — nothing to push"
    exit 0
fi
git -c user.name="VelocityBench Setup" -c user.email="evolution.digitale@gmail.com" \
    commit -q -m "Publish VelocityBench site — $(basename "$RUN")"
git push origin "$BRANCH"
echo "publish-site: pushed → https://evoludigit.github.io/velocitybench/"
