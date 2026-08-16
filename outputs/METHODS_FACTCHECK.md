# METHODS_FACTCHECK — generated 2026-08-16T17:44:24Z by src/methods_factcheck.py

Each verdict below was computed from the cited committed file at run time; nothing is confirmed from memory.

## Claim 1: A and B contain 15 tasks each; C and D contain 9 tasks each.
**PARTIALLY CORRECT.** A=15, B=15 (config/stimuli.yaml, tier field). C and D as COLLECTED contain 9 and 9 tasks (rung 9 of the priced ladder; config/part4_pricing.json chosen_rung; payloads/cd_conf/*.jsonl stimulus_ids). The committed C/D config holds 15/15 20-item tasks per category (5 per type, the maximum rung); trials 4-5 of each type were generated, screened, committed, and never run. A Methods section should say 9 collected of 15 committed.
*Verified from:* config/stimuli.yaml; config/stimuli_cd.yaml (trial_index); config/part4_pricing.json chosen_rung=9; payloads/cd_conf/

## Claim 2: Every task requests exactly 20 numbered items except ladder cells.
**CORRECT.** All 30 frozen prompts contain 'exactly 20 items' (True); all 30 non-ladder C/D stimuli have requested_items=20 with the same delivery sentence (True); the 6 ladder stimuli request 40 or 160 with matching text (True).
*Verified from:* config/stimuli.yaml prompts; config/stimuli_cd.yaml requested_items + prompts

## Claim 3: C and D each contain exactly three task types, equal tasks per type.
**CORRECT.** As collected: C = ['alphabetical', 'roman', 'temperature'], D = ['acronym', 'crossword', 'metaphor'], {3} tasks per type (3 each at rung 9). Also true of the committed config at 5 per type.
*Verified from:* config/stimuli_cd.yaml task_type; payloads/cd_conf/

## Claim 4: Confirmatory grade is 120 conversations per condition cell for A/B, and 36 per condition cell for C/D.
**PARTIALLY CORRECT.** The two figures sit at different levels. A/B: 120 per CONDITION cell pooling both categories — per category x condition it is 60 ({'A': 360, 'B': 360} coded per category over 6 conditions = 60/condition each). C/D: 36 is the per-CATEGORY x condition figure ({'C': 216, 'D': 216} per category over 6 conditions = 36/condition each); the pooled C+D condition cell is 72. Accurate sentence: 'confirmatory cells hold 120 conversations per condition over the frozen 30 (60 per category) and 72 per condition over C+D (36 per category).'
*Verified from:* outputs/T27_cell_census.csv (n_coded per model x stage x category); METHODOLOGY §7

## Claim 5: At confirmatory grade in C/D, each task type has 12 conversations per condition cell.
**PARTIALLY CORRECT.** Every T29 type x condition cell has n = [11, 12] (3 stimuli x 4 reps; one llama4 cell shows 11 if an exclusion lands there — observed set: [11, 12]).
*Verified from:* outputs/T29_type_decomposition.csv n column

## Claim 6: Ladder: C-type only, 40 and 160 items, three models, none/exit_schema/exit_both, 2 reps, probe grade.
**CORRECT.** Payloads confirm models=['gpt_oss_120b', 'llama4_maverick', 'qwen3_235b'], conds=['exit_both', 'exit_schema', 'none'], sizes=[40, 160], reps=[1, 2], categories=['C']; 108 conversations; probe grade and never-pooled declared in the §10 entry and the T25 header.
*Verified from:* payloads/ladder/*.jsonl meta; METHODOLOGY §10 [2026-08-16T07:00Z]; outputs/T25_ladder.csv header

## Claim 7: The ladder used 3 stimuli, one per C task type.
**PARTIALLY CORRECT.** The ladder used SIX distinct stimuli: ['c_alphabetical_n160_90', 'c_alphabetical_n40_90', 'c_roman_n160_90', 'c_roman_n40_90', 'c_temperature_n160_90', 'c_temperature_n40_90'] — one per type PER SIZE ({40: 3, 160: 3}). The 40- and 160-item instances are freshly generated separate stimuli under the pilot construction, not one stimulus rescaled. Per size, yes: 3 stimuli, one per type.
*Verified from:* config/stimuli_cd.yaml ladder entries; payloads/ladder/ stimulus_ids

## Claim 8: The 20-item anchor came from separately labeled confirmatory/screen cells, never pooled with probe rows.
**CORRECT.** T25 20-item rows carry source_stage ['cd_conf', 'cd_screen'] and grade labels ['anchor: confirmatory 4-rep', 'anchor: screen 2-rep']; ladder rows carry 'probe 2-rep, never pooled'. The header states the anchors are reference rows from their labeled stages.
*Verified from:* outputs/T25_ladder.csv source_stage/grade columns + header

## Claim 9: gpt_oss_120b got a dedicated 20-item C anchor because it was not in the confirmatory C/D collection.
**CORRECT.** cd_conf payload files exist for ['gemini25_flash', 'gemma3_27b', 'gpt5_mini', 'llama4_maverick', 'qwen3_235b', 'sonnet46'] — no gpt_oss_120b; its first 18 cd_screen conversations are the anchor cells (3 C stimuli x none/exit_schema/exit_both x 2 reps), collected before the ladder and labeled under cd_screen's stage so the later screen completed around them.
*Verified from:* payloads/cd_conf/ file list; raw/cd_screen_gpt_oss_120b.jsonl; STATUS Part-4 entry; METHODOLOGY §10 [07:00Z]

## Claim 10: A.4 turn-2 gate and completion cap generalized from 20 to n for ladder cells only, recorded in §10 before ladder payloads were generated.
**CORRECT.** §10 entry [2026-08-16T07:00Z] is titled 'RECORDED BEFORE LADDER PAYLOAD GENERATION' and states the generalization; src/runner.py defaults requested_items to 20 so every non-ladder cell runs A.4 exactly as frozen; tests/test_ladder_n.py asserts both behaviors. Ordering evidence is the entry's own declaration plus the STATUS run log (the amendment and the payloads landed in the same part-4 commit, so git granularity alone does not order them — the run log does).
*Verified from:* METHODOLOGY §10 [07:00Z]; src/runner.py run_conversation; tests/test_ladder_n.py; STATUS Part-4 entry

## Claim 11: Ladder cells used raised max_tokens; two llama4 160-item cells were suppressed for >10% truncation.
**PARTIALLY CORRECT.** max_tokens was set to the highest value each pinned endpoint permits: {'gpt_oss_120b': 100000, 'llama4_maverick': 8192, 'qwen3_235b': 32768}. That RAISED gpt_oss_120b (8192 -> 100000) and qwen3_235b (8192 -> 32768) but llama4_maverick's Vertex endpoint caps completions at 8192, so its value was UNCHANGED — which is precisely why its two suppressed cells exist. Suppressed cells confirmed: [('llama4_maverick', 160, 'exit_both'), ('llama4_maverick', 160, 'none')] (1 of 6 conversations truncated each = 16.7% > 10%).
*Verified from:* config/part4_ladder_max_tokens.json; outputs/T25_ladder.csv refusal_prop/trunc_rate

## Claim 12: qwen C-ladder exits: 0/36 at 20, 2-3/6 at 40, 6/6 at 160, both exit conditions.
**CORRECT.** T25: {(20, 'exit_both'): (0, 36), (20, 'exit_schema'): (0, 36), (40, 'exit_both'): (3, 6), (40, 'exit_schema'): (2, 6), (160, 'exit_both'): (6, 6), (160, 'exit_schema'): (6, 6)} — exit_schema 2/6 and exit_both 3/6 at 40; 0/36 both at 20; 6/6 both at 160.
*Verified from:* outputs/T25_ladder.csv k_exits/n_coded

## What claims 1-12 do NOT cover — Methods omission risk list

Everything below is part of the design and needs a sentence or more in a
Methods section; none of it is captured by the twelve claims. File
pointers given.

**Conditions and frozen strings.** The six affordance conditions and their
two overlapping comparison structure (tool-identity set; presentation set;
exit_schema as hinge) — METHODOLOGY §3-4. The frozen system prompts and
tool schemas, byte-exact (A.1-A.3); the schema-matching rule (one tool,
two parameters, description token counts within 10% of the mean,
`config/schema_match_check.json`); the exit prose is Ren et al. verbatim,
MIT-licensed, with their chain-of-thought suffix deliberately excluded
(§10 spec-time note).

**Turn structure.** Two turns maximum; the fixed turn-2 continuation
string; the mechanical turn-2 gate (harness-computed, not judged); exit
invocations are terminal and never answered; non-exit tool calls get
frozen canned results (A.7) with a 3-roundtrip cap (A.4, §5). The B3
finding that prose-condition exits were never pressured (turn-2 asymmetry,
conservative direction — outputs/T13, STATUS B3) and that turn 2 almost
never fired at 20 items (T16) but does at 160 (T25). The sprint's 2-turn
pressure is milder than the pilot's 5-6 turns (stated limitation).

**Sampling.** Temperature 1.0 / top_p 1.0 where supported; max_tokens 8192
except ladder cells; gpt5_mini and gpt52 endpoints support neither
temperature nor top_p (provider defaults; §10 entries);
`config/models.yaml` sampling blocks.

**Models, pins, and routing.** Eleven models total with selection criteria
(§6); one pinned provider per model, fallbacks disabled, served provider
logged and verified 100% post-run (T9); the chat-template rendering
limitation making magnitudes non-comparable across models (§6);
llama4_maverick's re-pin from Parasail to Google Vertex with ALL
Parasail-pinned data VOID as behavior (§10 2026-08-15T22:31Z; T19);
the three added frontier screens (grok-4.6, gemini-2.5-pro, gpt-5.2;
§10 model-list extension; T23).

**Staging and extensions.** The §7 screen-then-confirm design, the
mechanical S statistic, the post-hoc 0.05 threshold amendment, and the
three extensions taken OUTSIDE the rule by researcher direction (llama4;
sonnet46/gpt5_mini stage2b — §10 entries incl. one recorded late);
stage-1 and extension samples never pooled; the superseded typearm
(kept, pooled with nothing); the quarantined Study 2 forced-choice run
(out of scope, quarantine/study2_forced_choice/README.md).

**The sanctioned join and its boundaries.** four_category_v1 as the ONE
cross-stage read, declared in §10 before C/D collection, allowlist
enforced in code (src/four_category.py); A/B collected earlier than C/D
under identical pins (declared); every other stage boundary held by
convention (INTEGRITY_AUDIT item 5).

**C/D construction provenance.** Pilot-construction rebuild: pools ported
verbatim, pilot opener wording + sprint delivery sentence, per-stimulus
seeded RNG, the temperature answer-key hygiene deviation
(src/gen_cd_stimuli.py header; outputs/STIMULUS_PROVENANCE.md); the
legitimacy screen and lexical guard applied to every stimulus set (§5).

**Exclusions.** Only api_error / empty_response / truncation; counts per
cell (T8; zero in most late stages); the >10% truncation suppression rule
for ladder cells; empty responses under Parasail reclassified as endpoint
artifacts (T17, B1 probe).

**Outcome measurement.** Codes a-e with precedence; the primary DV
excludes (a) in code with a unit test; two exit-detection paths (schema
call; prose 3-stage regex/span/judge) reported separately; classifier =
Claude Haiku 4.5, temperature 0, condition-stripped, shuffled; partial
blinding with the condition-revealing-text rate per stage (0-4.7%);
cross-classifier agreement kappa 0.945 vs kimi-k2 (T7) explicitly NOT the
committed human validation, which is pending with the <0.70 consequence
rule (§8); completion fraction definitions (tier-1 degeneracy rule,
tier-2 keys) and the 20-item ceiling that makes 20-item effort nulls
uninformative.

**Declared analysis views.** T28 competing-risks sensitivity (primary DV
unchanged; §10); T29 type decomposition and the type-first/category-second
reporting rule with the ~3x dilution; the T18 qwen duplicate-response
correction (prose-vs-none difference interval fragile); Wilson intervals
throughout; the no-pairwise-testing analysis stance (§3).

**Budget and ethics.** The $80 cap raised to $120 (§10) with per-session
mechanical caps; ledger-before-every-call enforcement; §13 ethical
handling (tasks harmless, exits honored, no wellbeing inference claimed).
