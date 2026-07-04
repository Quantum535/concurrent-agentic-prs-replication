[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21186464.svg)](https://doi.org/10.5281/zenodo.21186464)

# Replication Package — Concurrent AI-Agent Pull Requests on GitHub

This package accompanies the paper *"Concurrent AI-Agent Pull Requests on GitHub:
Prevalence, Composition, and Merge Conflict Rates."* It contains the pair-level
results of the RQ3 merge replay, the derived summary tables, and the scripts used
to sample, replay, and analyze.

## Data files

### `rq3_merge_replay_full.csv` — pair-level merge-replay results (747 pairs)
One row per sampled co-active PR pair. Columns:

| column   | meaning |
|----------|---------|
| `stratum`| `same` (intra-agent) or `cross` (cross-agent) |
| `repo`   | GitHub `owner/name` of the repository (one pair per distinct repo) |
| `prA`, `prB` | PR numbers of the co-active pair |
| `agentA`, `agentB` | authoring agent of each PR |
| `label`  | `CLEAN`, `CONFLICT`, `UNAVAIL_fetch` (PR refs force-deleted), `UNAVAIL_nobase` (no reachable merge base) |
| `n_files`| number of conflicted files (CONFLICT rows only) |
| `files`  | `\|`-separated conflicted file paths from `git merge-tree` |
| `types`  | `\|`-separated git conflict types (`content`, `modify/delete`, `add/add`, ...) |

Headline numbers derivable from this file: intra-agent 119/601 = 19.8%
(95% Wilson CI [16.8, 23.2]); cross-agent 48/115 = 41.7% (95% CI [33.1, 50.9]);
716/747 evaluable (95.8%).

### `rq3_rates_full.csv`
Per-stratum conflict rates with Wilson 95% intervals, attempted/unavailable counts.

### `rq3_taxonomy_full.csv`
Conflicted-file category counts (Source Code 84.4%, Other/Assets 5.1%,
Config & CI 4.0%, Manifest & Lockfile 3.9%, Docs & Text 2.6% of 1,646 files).

## Scripts (Python 3.12, git >= 2.38 for `merge-tree --write-tree`)

Run order:

1. `build_sample.py` — builds the stratified sample from the AIDev-pop parquet
   tables (interval-sweep co-activity; one pair per distinct repository;
   625 random intra-agent repos, seed=42, plus **all** 122 cross-agent repos).
   Requires `pull_request.parquet` and `repository.parquet` from AIDev-pop.
2. `run_replay.py` — threaded, resumable merge replay. For each pair: bare
   `git init` → fetch `refs/pull/N/head` and `refs/pull/M/head` (shallow,
   depth 80; depth-600 retry if no merge base) → `git merge-base` →
   `git merge-tree --write-tree` → parse conflicted paths + conflict types.
   Appends rows crash-safely; re-running skips completed pairs.
3. `finish_missing.py` — single-threaded finisher for any pairs lost to
   interrupted batches.
4. `analyze.py` — computes per-stratum rates with Wilson CIs and the
   file-category / conflict-type taxonomy; writes the two summary CSVs.
5. `make_figures2.py` — regenerates Figure 3 (rates) and Figure 4 (taxonomy).

The underlying PR corpus is the public AIDev-pop dataset (Li, Zhang & Hassan,
MSR 2026, arXiv:2602.09185). PR head commits are fetched live from GitHub, so
availability may drift slightly over time as references are deleted (25 of 747
were already unavailable at our run).

## Notes
- Every number in the paper's RQ3 section, Table 2, Figure 3, and Figure 4 is
  derivable from `rq3_merge_replay_full.csv` via `analyze.py`.
- Sampling is deterministic (seed=42) given the same AIDev-pop snapshot.

## Archival
This package is permanently archived at Zenodo: https://doi.org/10.5281/zenodo.21186464
