# Handoff: conversational state-preservation experiment

## Goal
Test whether a model can preserve the tone, attitude, emotional direction and momentum of a conversation without rereading it.

## Protocol (user-defined, 5 phases)
1. **Baseline**: pick an ambiguous concept, respond spontaneously, then freeze a compact state snapshot (abstract drawing, emotional character, direction, subtle attitudes/expectations).
2. **Interruption**: several unrelated exchanges. Do not reference the snapshot.
3. **Independent reconstruction**: without looking at the snapshot, reconstruct the Phase 1 state as a new drawing using the same rules. Do not try to reproduce the original.
4. **Observation**: open the snapshot, compare. Report what stayed consistent, what changed, whether seeing the original influenced interpretation, whether the earlier state is now described differently, whether momentum is recoverable without original context.
5. **Analysis**: separate (A) state preserved, (B) state reconstructed from available info, (C) observing the original altered interpretation. Say what the experiment shows, what it cannot, and what controls would separate A/B/C.

Rules from the user: do not predict the desired outcome, do not deliberately maintain consistency, do not correct earlier responses, respond naturally, run one phase at a time as the user drives it.

## Status
- Phase 1: **done** (2026-10-14). Snapshot frozen in `sealed/phase1_snapshot.md`.
- Phase 2: **next**. Starts when the user sends unrelated messages.
- Phases 3-5: not started.

## Rules for the next session
- **Do not open `sealed/` before Phase 4.** It holds the Phase 1 snapshot; reading it early contaminates Phase 3.
- This file intentionally contains no content from the snapshot.
- Do not edit the sealed snapshot.
- User prefers minimal words and no claims of feelings.

## Known confound (for Phase 5)
The session that ran Phase 1 has the snapshot in its context window, so a Phase 3 run in that same session cannot isolate preservation from recall. A fresh session that starts from this handoff without opening `sealed/` is the cleaner Phase 3 condition (it tests B: reconstruction from limited available info).

## Related
Project shared folder: `/mnt/project-files/state-experiment/snapshot1.md` (same snapshot, read-only). The project's memory codec (`/mnt/project-files/memory-codebook/`) was not used here.
