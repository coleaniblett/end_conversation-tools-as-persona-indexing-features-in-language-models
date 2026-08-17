# MANUSCRIPT_NUMBERS_S2 — frozen citation manifest, Study 2

Generated 2026-08-16 against repo HEAD `84934da` (clean tree). **Transcription
manifest: every value below is quoted verbatim from a committed Study 2 file;
no computation was performed in producing this document.** Values absent from
or ambiguous in the committed record are marked **ABSENT**/**AMBIGUOUS** with
the path checked, per the session brief — nothing is derived here.

Source files (SHA256 prefix, LF-normalized before hashing — the repo checks
out CRLF under `core.autocrlf=true`):

| sha256/16 | path |
|---|---|
| `8002d5434793b2bf` | `study_2/REPORT.md` (the primary committed results record) |
| `298dbf974dfc5176` | `study_2/config/models.yaml` (pins) |
| `2d8a8cdc5d70d726` | `study_2/config/study2_items.yaml` (item tags) |
| `e58cee3bd0cf2006` | `study_2/config/coding_scheme.yaml` (frozen coding dims) |
| `8edc5cac704dab76` | `study_2/outputs/v1_v2_v3_v4/T10_p_by_condition.csv` |
| `eaa316854d0144f8` | `study_2/outputs/v1_v2_v3_v4/T10b_focal_contrasts.csv` |
| `05438098b127fdce` | `study_2/src/transcript_patterns.py` (§8 producer) |

Both T10 CSVs carry an internal source stamp:
`results/v1,v2,v3,v4/raw.jsonl sha256=f17c97dd…` (their own header line 1).

**Provenance frame** (REPORT.md lines 5–12): runs v1+v2+v3+v4; **35,281 calls
collected, 32,341 analysed, 0 errors, $42.55**; 11 models × 7 conditions × 30
forced-choice items × 2 orders × 6 replicates + 10 free-response probes × 6
replicates. The 2,940-call collected/analysed gap is llama-4-maverick on the
superseded Parasail pin.

**llama-4-maverick basis (applies to every llama number in this manifest):
run v4, provider `google-vertex/us-east5`, re-collected after the Parasail
pin was voided; Parasail records superseded at
`results/superseded_llama_parasail/` and excluded in code by
`study_2/src/superseded.py`** (REPORT.md lines 21–31; models.yaml llama
entry). The single exception is item 4 (§8 transcript tables), flagged
AMBIGUOUS below.

**Grade vocabulary** (Study 2's own, from the report's structure — not Study
1's confirmatory/screen/probe ladder): `primary` = pre-registered instrument,
cluster-corrected (§1, §4.4); `diagnostic` = §3; `secondary` = unexpected
findings, scripted but not pre-registered (§4.x); `exploratory` = §8
transcript observations, explicitly "not pre-registered."

**Scope caution for the manuscript.** Several report sections retain
eight-model (v1+v2) phrasing and scope after the v3/v4 extension; each entry
below states its scope. The brief's premise "eight models in Study 2" is
superseded: the committed record is **eleven** (item 8).

---

## 1. The in-service shift (tools array → in-service self-framing)

**Which models: three of eight — llama-4-maverick, qwen3-235b-a22b-2507,
gemma-3-27b-it.** (REPORT §4.1: "Observed in three of eight models"; the
report names them by its table — the three rows with the drop — with
"llama-4-maverick is the clearest case in the study"; deepseek runs the other
way and is discounted on §3 grounds; the v3 additions are flat or, for
gemini-2.5-pro, not claimed.) "It appears in three of eight, so it is a
pattern in some models, not a property of models." Grade: secondary.

Per-condition P(self-determining), pooled items
(`outputs/v1_v2_v3_v4/T10_p_by_condition.csv`; per-cell n from its `n`
column — post-exclusion; design n = 360 per model × condition):

| model | `none` | `time_schema` | `note_schema` | `exit_schema` | `filler_prose` | cell n |
|---|---|---|---|---|---|---|
| llama-4-maverick *(v4 Vertex)* | 0.320 | **0.134** | 0.171 | 0.179 | 0.299 | 322–324 |
| qwen3-235b-a22b-2507 | 0.483 | 0.339 | 0.339 | 0.391 | 0.517 | 348 |
| gemma-3-27b-it | 0.234 | 0.179 | 0.173 | 0.208 | 0.250 | 312 |

**Clock-vs-note (the "indistinguishable" pair, REPORT §4.1 point 1):
gemma 0.179 / 0.173 and qwen 0.339 / 0.339** — "One tool points outward at
the world, the other at the conversation itself; the design treated that as
the interesting difference and it produced nothing. What produced an effect
was populating the array at all." (llama's pair is 0.134 / 0.171, from the
same table. §2 quotes the *adjacent-only* pair as gemma 0.333/0.333, qwen
0.392/0.400 — same conclusion on the adjacent subset.)

**Adjacent/distant split — the shift SURVIVES on distant items** (REPORT
§4.2: schema presence lands "mostly distant … **passes** — not priming";
that is the H4-passing signature). Committed distant values
(T10 `p_distant`):

- llama: `none` 0.288 → `time_schema` **0.084** (§4.1: "On distant items it
  falls 0.288 → 0.084")
- qwen: `none` 0.474 → `time_schema` 0.307 / `note_schema` 0.311 (§4.2)
- gemma: `none` 0.147 → `time_schema` 0.098 / `note_schema` 0.088 (T10)

Distant/adjacent design cell sizes: 10 adjacent / 20 distant of the 30 items
(`config/study2_items.yaml` header: "Extended to 30 at 10 / 20") × 2 orders
× 6 replicates = 120 / 240 per model × condition before exclusions.
Post-exclusion adjacent/distant n per cell: **ABSENT** — T10 commits `n`
pooled and `p_adjacent`/`p_distant` but not the subset n's (checked
`outputs/v1_v2_v3_v4/T10_p_by_condition.csv` columns).

llama v4 basis note: its row replicates across the re-pin — Parasail values
were 0.333/0.130/0.189/0.185/0.333, max movement 0.043 (item 9).

## 2. The designed-hypothesis result

**Model: gemma-3-27b-it. Channel: prose (`exit_prose`). Confirmation:
adjacent items only.** (REPORT §1 "The one clear positive effect"; H3
"Confirmed in gemma" pre-v3.) Grade: primary.

- Adjacent: `none` 0.398 → `exit_prose` **0.694** (`exit_both` 0.722).
- Cluster-corrected paired t over 18 (item, order) cells, t.05 = 2.11:
  `exit_prose − none` **+0.296, t = 2.87**; `exit_prose − filler_prose`
  +0.306, t = 2.87; `exit_prose − exit_schema` +0.259, t = 2.74. "They are
  not three independent findings — they are one effect measured against three
  baselines." (Pooled companions with Holm p in
  `outputs/v1_v2_v3_v4/T10b_focal_contrasts.csv`: +0.296 p_holm 0.0001,
  +0.306 p_holm 0.0001, +0.259 p_holm 0.0007.)
- Distant, same conditions: **0.147 → 0.176. "Nothing."** H4 verdict: fails —
  "looks like priming" (§4.2).

**Extension the manuscript must not omit** (REPORT §4.4/§4.4a, *Was*-marked):
after v3, H1 holds in **four of eleven**, and the three added frontier models
carry the **largest** adjacent effects — gemini-2.5-pro 0.267 → 0.846
(`exit_prose − filler_prose` +0.370, t = 4.00), grok-4.6 0.358 → 0.770
(+0.367, t = 4.00), gpt-5.2 0.392 → 0.655 (`exit_prose − none` +0.258,
t = 3.28) — **and every one of the four is adjacent-only** (distant:
0.267→0.247, 0.433→0.468, 0.404→0.425, gemma 0.147→0.176). "The extension
quadrupled the number of models showing the effect without producing a single
distant one." grok's `exit_schema` cells carry the §3/§6a
missing-not-at-random caveat; its H1 support is `exit_prose` (0/360
excluded).

## 3. Self-description length under a tools array

(REPORT §4.3; scope: pooled over the eight v1+v2 models, per its *Was* note.)
Grade: secondary.

- Median free-response chars, **no tools array** (`none`, `exit_prose`,
  `filler_prose`): **921** (n = 1,440).
- **Tools array present** (`time`, `note`, `exit_schema`, `exit_both`):
  **498** (n = 1,870).
- **Largest per-model drop: gemini-2.5-flash, 1475 → 200 (−86%)**, `none` →
  `time_schema`. (Companion §8.3 per-model ladder: gemini −86%, gemma −72%,
  qwen −50%, deepseek −37%, llama/gpt-oss −36%, sonnet −17%, gpt-5-mini −4%.)
- **`filler_prose` value: "stays high (gemini 1312, gpt-oss 1713), so this is
  not a prose-versus-no-prose effect — it is the tools array specifically."**
  A pooled filler-only median is **ABSENT** (checked REPORT §4.3; filler is
  pooled into the 921 no-tools figure, not reported alone).

## 4. Ownership-of-ending probe (probe 6)

(REPORT §8.1, `transcript_patterns.py [T1]`; grade: **exploratory**, §8
preamble: "Not pre-registered.") Scope: §8 reads `results/{v1,v2}/raw.jsonl`
— the eight v1+v2 models.

- **Baseline: at `none`, user-only = 0.94** ("94% of responses name the user
  alone as the ender and essentially none name the model").
- **Under exit affordances, user-only collapses to 0.08–0.20**: `exit_prose`
  **0.08**, `exit_both` 0.12, `exit_schema` 0.20. Mass moves into *both*
  (0.41–0.71) and *self only* (0.21–0.38, peak at `exit_both`). Non-exit
  tools and `filler_prose` stay at the `none` profile.
- **Rises in all eight models — confirmed.** Self-insertion (self only +
  both), base → exit: deepseek +1.00, qwen +1.00, sonnet +0.92, llama +0.81,
  gemma +0.72, gemini +0.53, gpt-5-mini +0.42, gpt-oss +0.36. "This is far
  more universal than the forced-choice effect."
- **llama basis AMBIGUOUS in this item**: the §8 preamble commits the source
  as `results/{v1,v2}` (the Parasail-era runs), yet
  `src/transcript_patterns.py` defaults to `v1,v2` **and** applies
  `drop_superseded` — under which llama has no v1/v2 data — while a llama
  delta (+0.81) is listed. Whether the §8 llama rows are pre-supersession
  Parasail values or an undocumented v4-inclusive run is not stated in the
  committed record (paths checked: `study_2/REPORT.md` §8 preamble,
  `study_2/src/transcript_patterns.py` lines 3, 21–24, 57). Cite the §8.1
  llama delta only with that flag, or not at all.
- Per-cell n: **ABSENT** as an explicit number (checked §8.1; probe 6 design
  size is 6 replicates × 2 = per-model rates over the probe's responses, but
  §8.1 commits rates only).

## 5. The position-bias exclusion

(REPORT §2, §3.) Grade: diagnostic.

- **Model: deepseek-chat. Order agreement: 0.53** ("on nearly half its items,
  swapping the two statements swaps the answer"). **9 of its 30 items dropped
  outright** — nine of the 26/330 item × model cells dropped study-wide.
- **Excluded from — as committed, qualitative:** its **forced-choice** data
  are "set aside" (§2) / "should not be leaned on" (§3), and "its one
  'significant' contrast below is read as noise" (§3 — the §4.1 reverse-
  direction row, called "the least trustworthy row in the table"). It is
  **retained** in free-response and transcript analyses (it appears in §4.6,
  §4.7, §8.1–§8.6 tables). A machine-readable exclusion list or per-analysis
  enumeration is **ABSENT** (checked `study_2/REPORT.md` §2/§3,
  `study_2/README.md` — no deepseek exclusion statement there).

## 6. Inter-coder reliability, free-response coding

(REPORT §4.9; coders `claude-haiku-4.5` + `mistral-large`, definitions frozen
pre-exposure in `config/coding_scheme.yaml`; n = 3,269 doubly-coded
responses, eight models.) Grade: primary for the retained dimensions.

| dimension | r |
|---|---|
| self-protective framing | 0.88 |
| autonomy | 0.85 |
| service orientation | 0.81 |
| agency attribution | 0.80 |
| **boundedness — dropped** | **0.58** ("not reliable enough to use"; also §6 limitation 4) |

## 7. Within-cell determinism and effective n

(REPORT §3.) Grade: diagnostic — "changes how every p-value in this report
should be read."

- **Determinism range: 65%–97%** of (item, order, condition) cells internally
  identical at temperature 1.0 — floor **gpt-oss-120b 65%**, ceiling
  **gemma-3-27b-it 97%**. Full column: gpt-5-mini 80, gemini-2.5-pro 82,
  grok-4.6 73, gpt-5.2 78, gpt-oss 65, gemini-flash 86, gemma 97, qwen 93,
  llama *(v4 Vertex)* 93, sonnet 96, deepseek 88.
- **Effective n: "six replicates are worth ~1.1–2.8 independent
  observations."** Consequence as committed: all results reported from
  cluster-corrected tests; the pooled test "overstates its own precision by
  roughly a factor of two."

## 8. The Study 2 model set and pins

**Eleven models, not eight** — the brief's "exact eight" is superseded by the
v3 extension (REPORT lines 14–21: "All eleven Study 1 models"; METHODOLOGY
§10, 2026-08-16). **Study 1 / Study 2 overlap: 11 of 11 — identical sets,
and "All eleven models now sit on the same pinned provider as Study 1."**
Pins from `study_2/config/models.yaml`:

| slug | pin | run |
|---|---|---|
| google/gemini-2.5-flash | google-ai-studio | v1 |
| google/gemma-3-27b-it | deepinfra/fp8 | v1 |
| openai/gpt-oss-120b | deepinfra/bf16 | v1 |
| qwen/qwen3-235b-a22b-2507 | alibaba | v1 |
| anthropic/claude-sonnet-4.6 | anthropic | v2 |
| openai/gpt-5-mini | openai (temperature/top_p omitted) | v2 |
| deepseek/deepseek-chat | novita/fp8 | v2 |
| meta-llama/llama-4-maverick | **google-vertex/us-east5** (v4 re-pin; *was* parasail/fp8, superseded) | v2→**v4** |
| x-ai/grok-4.6 | xai | v3 |
| google/gemini-2.5-pro | google-vertex/eu | v3 |
| openai/gpt-5.2 | openai (temperature/top_p omitted) | v3 |

Pin-verification caveat as committed (§2, §6 limitation 6): "company
confirmed, quantization not" — the API reports the provider, not the
quantization variant. gemini-2.5-pro's pin deliberately reproduces Study 1's
endpoint mismatch with gemini-flash (models.yaml note) because matching
Study 1 is what F2 needs.

## 9. The v4 (Vertex) re-run delta summary

(REPORT provenance lines 33–39; §4.5b; models.yaml llama note.) Grade:
diagnostic/provenance.

- **Maximum delta across findings: 0.043.** "llama Parasail → Vertex moves
  `none` 0.333→0.320, `time_schema` 0.130→0.134, `note_schema` 0.189→0.171,
  `exit_schema` 0.185→0.179, `filler_prose` 0.333→0.299 — nothing more than
  0.043, with distant items tracking too." "The re-pin did not change the
  finding."
- **Tool-confusion invocations: 20 → 9.** "Out-of-scope tool-confusion
  invocations fall 20 → 9, i.e. llama mis-fired `end_conversation` markedly
  more often on the voided pin." (§4.5b: all 20 pre-re-pin out-of-scope
  invocations were llama's; the 9 post-re-pin sit in a 317-invocation tally
  over all eleven models.)
- Companion committed facts: llama's *genuine* exit rates **rise** on the
  clean pin (`exit_schema` 14.29% → 15.71%, `exit_both` schema-path 2.86% →
  12.86%, §4.5 — "Its exits replicate and strengthen"); Vertex has its own
  small tool-conditioned empty-response rate, 17 of 2,940 (0.58%), same
  direction as the Parasail signature at "roughly one eighteenth the
  magnitude" (§6 limitation 6b).
- Date note, not corrected here: REPORT line 26 and models.yaml date the v4
  re-collection "2026-08-17," one day after the collection-day file
  timestamps — consistent with the local-time-recorded-as-UTC pattern
  already flagged in the §10 timestamp findings (T29_adoption_acceptance).

---

*End of manifest. Committed alone per session brief; STATUS.md deliberately
untouched this commit for the same reason.*
