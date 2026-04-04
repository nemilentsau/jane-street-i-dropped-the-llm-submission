# Project Rules

## Required Skills

When working on the Svelte dashboard (`dashboard/`), you MUST use both skills:
- **analytical-dashboard** — for data visualization decisions, chart selection, layout, information hierarchy, color, and density
- **ux-design** — for visual design, typography, spatial composition, motion, and overall frontend aesthetics

Do not build or modify dashboard components without consulting these skills first.

## Mandatory Checks After Every Change

Run ALL of the following after making any code changes. Do not skip any.

### Python changes
```bash
.venv/bin/ruff check .
.venv/bin/pyright
```

### Dashboard (Svelte/TypeScript) changes
```bash
cd dashboard && npm run check
```

Fix all errors and warnings before considering the work done. Zero errors, zero warnings.

## Never Fabricate Data

Do not hardcode, invent, or assume results. Every number shown in the dashboard or any output must come from actually running the corresponding script. If a script hasn't been run, the data doesn't exist.

The project has real scripts in `pairing/`, `ordering/`, `distillation/`, and `e2e/` that produce real output. Use them.
