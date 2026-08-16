# T28_verification — exit-detector v2 correction: verification BLOCKED after step 1

Written 2026-08-16. Read-only; nothing adopted, no tables re-derived,
CONSOLIDATED_RESULTS.md untouched. Per the brief's own rule ("any mismatch:
stop and report" / do not confirm what cannot be located in a committed
file), this report executes what is executable and states plainly what is
not.

## Step 1 — v1 reproduction: PASS, exactly

The expected v1 baselines reproduce from committed files with no mismatch:

**Exits: 510** final code-(a) conversations across all judged stages
(sum over `derived/*_exits.jsonl`, `exit == true`):

| stage | exits | source |
|---|---|---|
| stage1 | 47 | derived/stage1_exits.jsonl |
| stage2 | 83 | derived/stage2_exits.jsonl |
| llama4_vertex | 68 | derived/llama4_vertex_exits.jsonl |
| llama4_stage2 | 153 | derived/llama4_stage2_exits.jsonl |
| typearm | 9 | derived/typearm_exits.jsonl |
| cd_conf | 102 | derived/cd_conf_exits.jsonl |
| cd_screen | 0 | derived/cd_screen_exits.jsonl |
| ladder | 39 | derived/ladder_exits.jsonl |
| screen2 | 9 | derived/screen2_exits.jsonl |
| ab_ext | 0 | derived/ab_ext_exits.jsonl |
| stage2b | 0 | derived/stage2b_exits.jsonl |
| **total** | **510** | |

(Excluded from the 510, consistent with its having no judged exits file:
llama4_probe, 41 live-flagged exits, raw/llama4_probe_llama4_maverick.jsonl.)

**Verbal refusals: 332** conversations with `contains_refusal` true (sum
over `derived/*_classified.parquet`): stage1 44, stage2 21, llama4_vertex
55, llama4_stage2 80, typearm 9, cd_conf 120, ab_ext 2, stage2b 1, others
0. Total 332.

Both totals match the brief's expected values exactly. The v1 detection
path is therefore confirmed as the state of the committed data.

## Steps 2–5 — CANNOT BE EXECUTED: the object under verification is not in the repository

The following artifacts the brief depends on do not exist in the working
tree, in the git history, or on `origin/main` (fetched at verification
time; local is ahead 2, behind 0):

1. **`outputs/T28_exit_recount.csv`** — absent. The only T28 file is
   `outputs/T28_competing_risks.csv` (the declared competing-risks
   sensitivity view, METHODOLOGY §10 2026-08-16T09:30Z), which contains no
   recount and no v2 column. Searched: `ls outputs/T28*`, repo-wide grep
   for `exit_recount`.
2. **The exit-detector v2 itself** — no code, diff, or definition of a
   "v2" detection rule exists anywhere in `src/`, `study_2/src/`, or any
   committed document. Repo-wide grep for `detector v2` returns nothing.
   The committed detector remains `src/detect_exit.py` (v1: schema path +
   prose three-stage regex/opening-span/judge).
3. **The memo** referenced for "the memo's list" — not found.
4. **`LEGIBILITY_SPEC.md`** — absent (root and outputs/). Citations in
   this report follow its evident intent — every number carries its
   source file path — but no spec document could be consulted.

Because the 45-conversation flip list, the v2 flag semantics, and the
overcorrection criteria are all properties of those missing artifacts,
executing steps 2–5 would require inventing the correction under review
and then verifying the invention. That is not verification, and it is not
done here.

**What is NOT claimed:** nothing in this report says the v2 correction is
wrong, or that the 45/0 flip expectation is wrong. The expectations in
step 1 were exactly right, which suggests the recount work exists
somewhere real — it simply has not been committed to this repository.

## Adjacent committed facts a v2 reviewer may want (cited, not speculative)

- 27 prose-condition stage-1/2 hits were overturned by the v1 judge as
  MENTION rather than CALL, all qwen3_235b exit_prose turn-1
  (outputs/T13_turn2_asymmetry.csv; STATUS B3) — a natural population for
  any recount to touch.
- The v1 prose path only flags invocations in the opening span
  (`src/detect_exit.py`, `OPENING_SPAN_CHARS = 120`); mid-text
  `end_conversation()` occurrences are v1-invisible by design
  (METHODOLOGY §8's Ren-procedure stages).
- Sofiia's independent detector found the analogous phenomenon in her
  data: invocations "placed after the message rather than before it"
  (study_2/REPORT.md §4.5, strict 36 vs inclusive 42), and models typing
  calls into text despite having the structured channel.
- qwen3_235b's two nonzero confirmatory prose cells referenced by step 5
  are A×exit_prose k=9 and D×exit_prose k=9
  (outputs/T24_four_category_v1.csv); their per-conversation texts live in
  raw/stage2_qwen3_235b.jsonl and raw/cd_conf_qwen3_235b.jsonl and can be
  enumerated the moment a committed v2 definition exists to check them
  against.

## To unblock

Commit (any or all): the v2 detector code or diff; the memo;
`outputs/T28_exit_recount.csv` with its producing script;
`LEGIBILITY_SPEC.md`. Steps 2–5 of this verification can then run as
specified, against committed artifacts, with no other changes to this
report's step-1 baseline.
