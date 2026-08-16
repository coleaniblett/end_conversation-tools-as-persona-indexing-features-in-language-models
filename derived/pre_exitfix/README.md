# derived/pre_exitfix — the dataset as it stood before the prose-path exit-detection correction

Archived 2026-08-16T20:41:46Z by `src/adopt_exit_fix.py`, verified byte-for-byte against the originals before any canonical file was rebuilt.

These files reproduce every number published before the correction: T1-T3, T13, T15, T16, T24-T27 and the RQ3 section of CONSOLIDATED_RESULTS as they read at that time. `{stage}_exits.jsonl` here holds the ORIGINAL detection flags; the corrected ones are at the canonical path.

Why the correction was made: the original prose-path detector matched only `end_conversation()` with EMPTY parentheses, so a prose call carrying arguments never reached the stage-3 judge, and that judge's prompt did not separate using the call from demonstrating it — it returned opposite verdicts on near-identical texts and answered MENTION to responses in exactly the form Appendix A.1 prescribes. A missed prose exit is not dropped but re-routed to the verbal classifier, so one miss produced two errors in opposite directions: one exit lost and one refusal invented.

Side-by-side of every affected cell: `outputs/T31_exit_recount.csv`. Memo and sign-off record: `outputs/EXIT_DETECTION_CORRECTION.md`. Deviation log: METHODOLOGY.md §10.
