# SUPERSEDED — llama-4-maverick on Parasail (Study 2 runs v1+v2)

**These data are not used in any report, table or figure.** They are kept
because `results/` is append-only and because a superseded measurement is still
a record of what was measured.

2940 records, extracted 2026-08-17 from `results/v2/raw.jsonl`, which is
itself left byte-identical (sha256 verified before and after this extraction:
`9115c97f83f17f12`). So these records exist in two places and are excluded from
analysis in one way: `src/superseded.py`, which every analysis entry point
imports and which matches on the SERVED provider rather than the run id.

## Why they are superseded

Study 2 pinned this model to `parasail/fp8`. Study 1 **voided its own
Parasail llama data as a serving-stack artifact** — 44 of 240 tool-condition
conversations came back empty against 0 of 120 tool-free — and re-pinned to
`google-vertex/us-east5` (METHODOLOGY §10, 2026-08-15T22:31Z). Study 2 had
therefore been measuring this model on the one backend its companion study had
already rejected, which meant the F2 cross-study linkage compared Vertex
behaviour against Parasail behaviour for the single strongest model in Study 2.

The original justification for Parasail was that Vertex does not declare a
quantization. That was the wrong trade: an undeclared quantization is a stated
limitation, whereas a pin the companion study voided is a confound.

Note that these records show **no sign of the failure mode that voided Study 1's
Parasail cells** — 0 errors across the run. "Not known to differ" is not the
same as "known to match", and the linkage needs the second.

## Replacement

Run `v4`, same model, same design, `google-vertex/us-east5`, collected
2026-08-17. Everything the report says about llama-4-maverick comes from v4.
