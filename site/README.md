# VelocityBench site

An explorable, self-contained benchmark explainer: point it at one run's JSON
and it renders a static page that answers *"which framework for my workload
shape, and why?"* — with the honesty devices load-bearing and visible.

The generator is **Python standard library only** (no npm, no build framework,
no new venv). One run JSON in → a deterministic, byte-stable static site out.

## Build

```bash
python site/build.py <run.json> --out site/dist
```

- `<run.json>` — exactly one benchmark run. The publishable build uses the
  median-of-three: `reports/hetzner-2026-07/bench-hetzner-2026-07-07-median.json`.
- Writes three files to `--out`: `index.html` (self-contained, offline,
  light/dark, no-JS fallback), `data.json` and `llms.txt` (the AI layer).
- `--costs <prices.yaml>` overrides the cost-composite price file
  (default `costs/instance-prices-2026-07.yaml`).

`site/dist/` is gitignored — it is always rebuilt from the run JSON.

## Test

```bash
tests/qa/.venv/bin/python -m pytest site/tests/
```

Tests are parametrized over two fixtures: the shipping median-of-three and
`bench-hetzner-2026-07-05-sweep3.json` (kept permanently as a regression net).
Structural honesty invariants must hold for both; value-specific pins live in
the per-section tests. Logic is tested, pixels are not.

## The same-run rule

`build.py` takes **exactly one** run JSON and refuses two — no cross-run or
cross-hardware mixing. Run identity (host, date, kernel, PostgreSQL and
framework versions, tview mode, trigger scope, median-of-N provenance) is shown
on the page. If the run targeted `localhost`, a **LOCAL DATA — NOT PUBLISHABLE**
banner is stamped automatically.

Every number on the page is also in the run JSON: no hand-typed figures, no
chart-only values. Derived figures (the cost composite, the amortization model)
show their formula and inputs.

## The scenarios.json contract

`site/scenarios.json` is the hand-maintained metadata layer the run JSON does
not carry: the canonical framework/scenario order, the structural
exclusions-by-design (with verbatim numbered reasons), mechanism/ladder/APQ/
cache/amortization configuration, workload-shape scoring, and the honesty
prose ("Reading these numbers").

Every `(framework, scenario)` cell resolves to one of three states, cross-checked
against this contract:

- **result** — measured, present in the run's `results[]`;
- **excluded by design** — structural, with its verbatim reason (never "slow");
- **not measured in this run** — wired but not executed in the run shown
  (distinct from excluded). A full run leaves none.

A result that collides with a by-design exclusion fails the build loudly —
the grid can never silently drift.

## Layout

- `build.py` — the generator (load → grid model → render).
- `svg.py` — hand-rolled chart helpers (nice axes, linear/log scales).
- `scenarios.json` — the metadata contract above.
- `templates/` — `base.html`, `site.css`, `llms.txt.tmpl`.
- `tests/` — the contract tests (run under `tests/qa/.venv`).
