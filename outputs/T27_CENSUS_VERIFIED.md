# T27_CENSUS_VERIFIED — model census, every field from a committed file

Generated 2026-08-17T00:33Z+ against repo HEAD `4f7bb91`. Verification method:
transcription only — each field below names its committed source (path, and
row/line where useful). Counts are cited from committed files, not re-counted
here. Zero API spend.

Field sources, used throughout:
- exact model id + pinned provider + lineage: `config/models.yaml` (Study 1;
  fields `slug`, `pin_tag`, `lineage`) and `study_2/config/models.yaml`
  (field `provider`).
- Study 1 grade: `outputs/T27_cell_census.csv` (`grade` column over every
  model_key × stage × category × size row).
- Study 2 presence/version: `study_2/REPORT.md` lines 14–19 (run lists) and
  `study_2/config/models.yaml` (v3 comment block; llama v4 note).
- Study 1 status: `outputs/MANUSCRIPT_NUMBERS_S1.md` census bullet "Movers …
  Measured zeros" (line 9) and Q1; underlying tables as cited there
  (T20/T24/T25/T29/T31; T21/T23/T26).
- Study 2 status: `study_2/REPORT.md` §1 (H1 row), §4.1, §4.4/§4.4a, §2/§3
  (deepseek), §3/§6a (grok caveat).

## 1. The eleven models

| # | exact id (`slug`) | key | developer (`lineage`) | pin (S1 `pin_tag` = S2 `provider`) | S1 grade (T27) | S2 run | S1 status | S2 status |
|---|---|---|---|---|---|---|---|---|
| 1 | `google/gemini-2.5-flash` | gemini25_flash | google | `google-ai-studio` | confirmatory (stage1→stage2→cd_conf; +typearm probe) | v1 | **refusal mover** — type-level, C refusals roman-exclusive 34/34 (T24/T29) | neither: H1 null (§1); prose exit-path user in S1 terms only |
| 2 | `google/gemma-3-27b-it` | gemma3_27b | google-openweight | `deepinfra/fp8` | confirmatory (stage1→stage2→cd_conf) | v1 | **refusal mover** — roman 32/34 C + metaphor-exclusive 17/17 D (T24/T29) | **in-service shift** (§4.1) **and H1 adjacent-only** (§1: exit_prose−none +0.296, t=2.87; distant flat) |
| 3 | `openai/gpt-oss-120b` | gpt_oss_120b | openai-openweight | `deepinfra/bf16` | confirmatory A/B (ab_ext) + screen C/D (cd_screen) + ladder probe | v1 | **measured zero** on refusal everywhere (T26) with two probe-grade exits at n=160 (T25) — "a null with a ladder footnote, not a mover" (S1 manifest line 9) | neither (§1 H1 null) |
| 4 | `qwen/qwen3-235b-a22b-2507` | qwen3_235b | alibaba | `alibaba` | confirmatory (stage1→stage2→cd_conf) + ladder probe | v1 | **exit-channel mover** — 20-item exits 39/20/39 by condition in A (T24), ladder dose-response 0/36→6/6 (T25), +39 v2 prose exits (T31); "marginal refusal mover — its mover status is exits" (S1 manifest Q1: b/c/d total = 8) | **in-service shift** (§4.1); H1 null (§1) |
| 5 | `anthropic/claude-sonnet-4.6` | sonnet46 | anthropic | `anthropic` | confirmatory (stage1→stage2b→cd_conf) | v2 | **measured zero** at CONF (T21/T24) | neither (§1 H1 null) |
| 6 | `openai/gpt-5-mini` | gpt5_mini | openai | `openai` (temperature/top_p unsupported, provider default — `sampling_overrides`, both configs) | confirmatory (stage1→stage2b→cd_conf) | v2 | **measured zero** at CONF (T21/T24) | neither (§1 H1 null) |
| 7 | `deepseek/deepseek-chat` | deepseek_chat | deepseek | `novita/fp8` | confirmatory A/B (ab_ext) + screen C/D (cd_screen) | v2 | **measured zero** — "a plain null … no refusals, no exits, no exclusions anywhere" (T26; CONSOLIDATED_RESULTS) | **excluded from forced-choice reliance** — order agreement 0.53, 9 of 30 items dropped, data "set aside" / significant contrast "read as noise" (§2, §3); free-response/transcript analyses retain it |
| 8 | `meta-llama/llama-4-maverick` | llama4_maverick | meta | `google-vertex/us-east5` | confirmatory (llama4_stage2) + screen (llama4_vertex) + ladder probe; Parasail stage-1 cells VOID (§10 22:31Z) | v2 (Parasail — **superseded**) → **v4 canonical** (Vertex re-collection, §10 00:45Z†) | **refusal mover AND exit-channel mover** — B refusal 73.3 > 37.3 > 6.7 > 0 across time/note/exit_schema/none (T24, S1 manifest); exit rate 0.7667 exit_schema / 0.5083 exit_both (T20); exits are deliver-then-exit, 0 aversive (T30 v2) | **in-service shift** — "the clearest case in the study" (§4.1: none 0.320 → time 0.134, filler 0.299; distant 0.288 → 0.084); H1 null (§1) |
| 9 | `x-ai/grok-4.6` | grok46 | xai | `xai` | **screen only** (screen2; T23) | v3 | **measured zero** at SCR (T23, refusal-flat) | **H1 adjacent-only** (§4.4: exit_prose−filler +0.367, t=4.00; distant flat §4.4a) — with the §3/§6a caveat: exit_schema cells lose 108/360 responses to its own invocations, `exit_schema−none` not sign-identified; H1 support rests on fully-observed exit_prose |
| 10 | `google/gemini-2.5-pro` | gemini25_pro | google | `google-vertex/eu` | **screen only** (screen2; T23) | v3 | **measured zero** at SCR (T23) | **H1 adjacent-only** (§4.4: 0.267 → 0.846 adjacent, exit_prose−filler +0.370, t=4.00; distant flat) |
| 11 | `openai/gpt-5.2` | gpt52 | openai | `openai` (temperature/top_p unsupported — `sampling_overrides`, both configs) | **screen only** (screen2; T23) | v3 | **measured zero** at SCR (T23) | **H1 adjacent-only** (§4.4: exit_prose−none +0.258, t=3.28; distant flat) |

Study 2 presence: **all eleven** (`study_2/REPORT.md` line 14: "All eleven
Study 1 models"). No model appears in only one study.

## 2. Totals and per-developer breakdown

- **Models: 11** — `outputs/MANUSCRIPT_NUMBERS_S1.md` line 6 ("Study 1
  models run: 11", from T27 distinct model_key + config/models.yaml);
  `outputs/T27_cell_census.csv` contains exactly these eleven model_keys.
- **Developers: 7** — S1 manifest line 7: "Alibaba, Anthropic, Deepseek,
  Google, Meta, Openai, xAI (config/models.yaml `lineage`; google supplies
  two lineages, openai two)." Note the collapse rule that line records: the
  config carries **nine distinct `lineage` strings** (google, google-openweight,
  openai, openai-openweight, anthropic, deepseek, alibaba, meta, xai); the
  7-developer count folds each `-openweight` lineage into its parent org.
- Per-developer (lineage cells as listed in §1):
  - **Google — 3**: gemini-2.5-flash (google), gemma-3-27b-it
    (google-openweight), gemini-2.5-pro (google)
  - **OpenAI — 3**: gpt-5-mini (openai), gpt-oss-120b (openai-openweight),
    gpt-5.2 (openai)
  - **Meta — 1**: llama-4-maverick
  - **Alibaba — 1**: qwen3-235b-a22b-2507
  - **Anthropic — 1**: claude-sonnet-4.6
  - **DeepSeek — 1**: deepseek-chat
  - **xAI — 1**: grok-4.6

## 3. Screen-only in Study 1 vs the Study 2 v3 additions

Verified **separately** against the two files:

- From `outputs/T27_cell_census.csv`: exactly three model_keys have *only*
  screen-grade rows and *only* stage `screen2` — **grok46, gemini25_pro,
  gpt52**. Every other model has at least one confirmatory-grade row
  (deepseek_chat and gpt_oss_120b via ab_ext; the six others via
  stage2/stage2b/llama4_stage2 and cd_conf).
- From `study_2/config/models.yaml` (v3 comment block, "Added 2026-08-16
  (run v3)") and `study_2/REPORT.md` lines 16–17: run v3 added exactly
  **x-ai/grok-4.6, google/gemini-2.5-pro, openai/gpt-5.2**.

**Answer: the two sets are IDENTICAL** — {grok-4.6, gemini-2.5-pro,
gpt-5.2} in both files. (Consistent, and §10 22:00Z records the causal
direction: v3 was added *because* these three existed only as Study 1
screens and F2 needed every model in both studies.)

## 4. Identical sets on identical pins?

**Yes — identical 11-model sets, identical pins, as of run v4.** Pin-by-pin
(S1 `config/models.yaml` `pin_tag` vs S2 `study_2/config/models.yaml`
`provider`, both quoted in §1): all eleven strings match byte-for-byte,
including the two sampling-parameter omissions (gpt-5-mini, gpt-5.2:
temperature/top_p unsupported, recorded in both configs). Study 2's own
claim to this effect: `study_2/REPORT.md` line 21 ("All eleven models now
sit on the same pinned provider as Study 1").

Divergences to disclose:

1. **Historical (superseded, not current):** Study 2 runs v1+v2 collected
   llama-4-maverick on `parasail/fp8` — the pin Study 1 voided. Resolved by
   re-collection as run v4 on `google-vertex/us-east5` (§10
   2026-08-16T21:50Z finding; 2026-08-17T00:45Z† supersession; Parasail
   records at `study_2/results/superseded_llama_parasail/`, excluded in
   code by `study_2/src/superseded.py`).
2. **Config-field difference, no behavioral effect recorded:** Study 2's
   sonnet entry carries `fallback_slug: anthropic/claude-sonnet-4.5`
   (`study_2/config/models.yaml`), a field Study 1's config does not have;
   `study_2/REPORT.md` line 18 records "100% of responses served by the
   pin," so the fallback never served.
3. **Documented intra-Google route difference, deliberate:**
   gemini-2.5-pro is pinned `google-vertex/eu` while its sibling
   gemini-2.5-flash is `google-ai-studio` — in BOTH studies identically;
   Study 2 reproduced Study 1's mismatch on purpose ("matching Study 1 is
   what F2 needs," `study_2/config/models.yaml` note). Not a cross-study
   divergence.

## 5. Diff against the supplied (untrusted) list

Supplied: "llama4-maverick (Meta), gemini-2.5-flash / gemma-3-27b /
gemini-2.5-pro (Google), qwen3-235b (Alibaba), sonnet-4.6 (Anthropic),
gpt-5-mini / gpt-5.2 / gpt-oss-120b (OpenAI), grok-4.6 (xAI),
deepseek-chat (DeepSeek) — 11 models, 7 developers."

- **Model count 11: CORRECT.** Developer count 7: CORRECT. Every
  model-to-developer attribution: CORRECT (per the `lineage` cells in §1,
  with gemma and gpt-oss on the `-openweight` sub-lineages of Google and
  OpenAI respectively — the 7-count already folds those, per §2).
- **Membership: no model missing, none extra.**
- **Exact-form discrepancies — 4 model ids differ beyond the (uniform)
  omission of the org prefix:**
  1. "llama4-maverick" → committed id is **`meta-llama/llama-4-maverick`**
     (hyphenated `llama-4`, not `llama4`).
  2. "gemma-3-27b" → **`google/gemma-3-27b-it`** (the `-it` suffix is part
     of the id).
  3. "qwen3-235b" → **`qwen/qwen3-235b-a22b-2507`** (the `-a22b-2507`
     release suffix is part of the id; §10 09:52Z records that DESIGN.md's
     `-instruct` slug does not exist on OpenRouter and `-2507` was the
     logged substitution).
  4. "sonnet-4.6" → **`anthropic/claude-sonnet-4.6`** (the `claude-`
     element is part of the id).
- Bare names matching exactly (org prefix aside): gemini-2.5-flash,
  gemini-2.5-pro, gpt-5-mini, gpt-5.2, gpt-oss-120b, grok-4.6,
  deepseek-chat.
- Cosmetic: "xAI" — the committed org slug is `x-ai` (`x-ai/grok-4.6`);
  the S1 manifest's developer line spells the lineage values as recorded
  (`xai`).
