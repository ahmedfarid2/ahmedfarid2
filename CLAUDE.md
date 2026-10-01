# ahmedfarid2

GitHub profile README repository (README, CV PDF, contribution-snake and profile-stats workflows). No build. Validate by parsing the workflow YAML and checking README links.

## Repository facts

**What it is.** GitHub profile repository: `README.md` is rendered on github.com/ahmedfarid2. Also holds the CV PDF and two automation pieces (snake workflow, stats workflow).

**Stack.** Markdown README; GitHub Actions (`.github/workflows/snake.yml` publishes a contribution-snake SVG to the `output` branch daily; `.github/workflows/stats.yml` publishes `github-metrics.svg` to the same branch every 12 hours).

**Structure.**
- `README.md` — the product; badges, links and embedded images must stay valid
- `Ahmed_Farid_CV.pdf` — binary; replace, never edit
- `.github/workflows/snake.yml` — `contents: write` permission; publishes `dist/snake.svg` to branch `output`
- `.github/workflows/stats.yml` — `contents: write` permission; renders the metrics card and publishes it to branch `output`. Both publishers use `keep_files: true` and share a concurrency group so neither wipes the other's files; never point them back at `main` (bot commits there flooded the profile's history, see #152)
- No top-languages card: it was removed because it only counts public repos (mostly exported HTML) and misrepresented the stack; don't re-add it without a token that covers private repos

**Conventions.**
- Workflow permission changes are infrastructure changes.
- README links point at the live portfolio and CV; verify URLs still resolve when touching them.

**Sensitive areas (treat changes as higher blast radius).**
- `.github/workflows/snake.yml`, `.github/workflows/stats.yml` (write permission)
- `README.md` (public profile)

**Validation commands.**
- `python3 -c "import yaml,sys; [yaml.safe_load(open(f)) for f in ('.github/workflows/snake.yml','.github/workflows/stats.yml')]"` — workflow YAML parses (PyYAML is available in the cloud environment; skip if absent)
- Render check — preview `README.md` and verify every link and image URL resolves; disclose as manual if not done

## Engineering orchestration

@.claude/orchestration/POLICY.md

Project-specific inputs to that policy are the sections above: **Sensitive areas** get `standard-reviewer` (or `critical-reviewer` on a critical path) before COMPLETE, and **Validation commands** are what to run and report verbatim, with skipped manual checks listed under "Manual checks required".
