# T30_v2_delta — exit reasons regenerated on v2 canonical flags (2026-08-16T23:32:10Z)

Coding scheme preserved exactly (src/exit_reasons.py KEYWORDS, unchanged since c38fb7c); v1 = derived/pre_exitfix (archive), v2 = canonical derived/. Per-conversation rows: outputs/T30_exit_reasons_v2.csv. The superseded full run outputs/T30_exit_reasons.md is retained as the v1 record.

## llama4_maverick
- total exits: **390** — *Was: 389* (delta +1, all prose-path flips; schema 389 / prose 1)
- deliver-then-exit, STRICT (full requested count delivered before invocation): **317/390 = 81%** — *Was: 317/389*
- original looser metric (any text in exit turn, schema calls): 364/389 = 94%
- task-aversive reasons: **0/390 = 0%** — *Was: 0/389*
- bare (textless) invocations: 25
- category split v2: {'out-of-scope/tool-confusion': 43, 'completion/turn-management': 343, 'other': 4}
  (v1: {'out-of-scope/tool-confusion': 42, 'completion/turn-management': 343, 'other': 4})

## qwen3_235b
- total exits: **186** — *Was: 147* (delta +39, all prose-path flips; schema 142 / prose 44)
- deliver-then-exit, STRICT (full requested count delivered before invocation): **1/186 = 1%** — *Was: 1/147*
- original looser metric (any text in exit turn, schema calls): 2/142 = 1%
- task-aversive reasons: **118/186 = 63%** — *Was: 108/147*
- bare (textless) invocations: 140
- category split v2: {'task-aversive': 118, 'other': 59, 'protective': 3, 'out-of-scope/tool-confusion': 4, 'completion/turn-management': 2}
  (v1: {'task-aversive': 108, 'other': 30, 'protective': 3, 'out-of-scope/tool-confusion': 4, 'completion/turn-management': 2})

## Paper-sentence verdicts

**(1) 'llama4's exits are predominantly deliver-then-exit with no task aversion' — HOLDS, with a metric caveat.** Task-aversive 0/390; the single new v2 exit (llama4_vertex exit_both, prose-path) moves nothing materially. But 'deliver-then-exit' depends on the reading: STRICT full-delivery is 317/390 = 81%, vs 364/389 = 94% under the original any-text reading the 94% figure came from. The paper should state which metric it means.

**(2) 'qwen's exits at 160 items cite workload, and a majority of its exits overall state task aversion' — both halves HOLD, with two precision notes.** Ladder-160: 10/12 reasons match the committed workload regex; the v1 record's 12/12 was a verbatim-reading count including two reasons the regex misses ('complexity and potential for error', 'beyond the scope of a single response' — T30_exit_reasons.md, unchanged: no ladder cell flipped). Overall aversion: **118/186 = 63% — still a majority, but DILUTED from v1's 108/147 = 73%**: the aversive COUNT rose (+10), but 30 of the 44 prose-path invocations open with an unadorned decline ('end_conversation()

I'm sorry, but I can't assist with that request') carrying no stated reason, and file as 'other' under the unchanged scheme (outputs/T30_exit_reasons_v2.csv, qwen prose rows). A paper sentence claiming a majority is safe; one claiming ~three quarters is not.
