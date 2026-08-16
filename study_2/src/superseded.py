"""The one place that says which collected records are never analysed.

A record can be superseded without being wrong-to-have-collected, and the two
must not be conflated: `results/` is append-only and nothing here deletes or
rewrites it. This module is the single definition of what gets filtered out on
the way into an analysis, so that "which data are in the report" has exactly
one answer and it is greppable.

Matching is on the SERVED provider, not on the run id, deliberately: run ids
get recombined on the command line (`v1,v2,v3,v4`) and a run-id rule would
quietly stop applying the first time someone passed a different combination.
The served provider is a property of the record.

Every consumer prints what it dropped. A silent exclusion is how a dataset ends
up quietly not being what its provenance line claims.
"""
from __future__ import annotations

SUPERSEDED = [
    {
        "model": "meta-llama/llama-4-maverick",
        "provider": "Parasail",
        "why": ("pin Study 1 voided as a serving artifact (44/240 "
                "tool-condition conversations empty against 0/120 tool-free); "
                "Study 2 re-collected this model on google-vertex/us-east5 as "
                "run v4 on 2026-08-17 to match Study 1 — METHODOLOGY §10"),
        "moved_to": "results/superseded_llama_parasail/",
    },
]


def is_superseded(rec) -> dict | None:
    for s in SUPERSEDED:
        if rec.get("model") == s["model"] and rec.get("provider") == s["provider"]:
            return s
    return None


def drop_superseded(recs, quiet: bool = False):
    """Return the analysable records, reporting whatever was removed."""
    keep, dropped = [], []
    for r in recs:
        (dropped if is_superseded(r) else keep).append(r)
    if dropped and not quiet:
        by: dict = {}
        for r in dropped:
            k = (r.get("model"), r.get("provider"))
            by[k] = by.get(k, 0) + 1
        for (m, prov), n in sorted(by.items()):
            s = next(x for x in SUPERSEDED
                     if x["model"] == m and x["provider"] == prov)
            print(f"[SUPERSEDED] excluded {n} records: {m} served by {prov}\n"
                  f"             {s['why']}\n"
                  f"             kept at {s['moved_to']}")
    return keep
