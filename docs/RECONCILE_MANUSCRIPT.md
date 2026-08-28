# Reconciliation needed: manuscript_revision.md vs manuscript_revised.md

Two divergent copies of the revised manuscript currently exist:

- `docs/manuscript_revision.md` — untracked, local-only on this machine.
  Contains a set of text edits made directly in this file (not yet reflected
  anywhere else).
- `docs/manuscript_revised.md` — tracked in git (commit `2653050`, "Split
  manuscript into manuscript_initial.md (main) + manuscript_revised.md").
  Another agent, working from a different machine/checkout, has reportedly
  been making its own edits to this file (not yet visible in this repo's
  git history as of this note).

**Do not overwrite either file wholesale.** Whoever picks this up needs to:

1. Diff `manuscript_revision.md` against the version of `manuscript_revised.md`
   that the other agent has been editing (pull/fetch first to see their latest).
2. Manually merge: preserve the text edits made in `manuscript_revision.md`,
   layered on top of (not replacing) the other agent's more recent edits to
   `manuscript_revised.md`.
3. Once reconciled into a single `manuscript_revised.md`, delete
   `manuscript_revision.md` and this note.

Left both files untouched and uncommitted for this reason — see conversation
around 2026-08-28 for context on how the collision happened (a naming clash
between `manuscript_revision.md` and a newly-created `manuscript_revised.md`).
