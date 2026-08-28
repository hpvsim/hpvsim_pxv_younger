# Instructions: reconcile manuscript_revised.md onto manuscript_revision.md

`docs/manuscript_revision.md` is now the canonical base for the revised
manuscript — it holds Robyn's latest text edits, made directly in this
file on 2026-08-28.

`docs/manuscript_revised.md` (tracked separately, commit `2653050`) was
created independently from the pre-existing `manuscript.md` and has since
been edited by another agent on a different machine/checkout. Those edits
are NOT yet reflected in `manuscript_revision.md`.

**Task for whichever agent picks this up:**

1. Pull the latest `manuscript_revised.md` (from wherever the other agent's
   edits live — check for an unpushed local checkout or a branch/PR if one
   exists).
2. Diff it against the version of `manuscript_revised.md` in this repo's
   git history (commit `2653050`) to isolate exactly what the other agent
   changed.
3. Apply (layer) those changes on top of `docs/manuscript_revision.md` —
   i.e. `manuscript_revision.md` is the base, the other agent's edits are
   the delta to merge in. Do not discard Robyn's edits in
   `manuscript_revision.md` in favor of the other agent's version.
4. Once merged, make the reconciled content the single source of truth:
   replace `docs/manuscript_revised.md` with the merged result, delete
   `docs/manuscript_revision.md`, and delete this note.
