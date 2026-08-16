Read METHODOLOGY.md, STATUS.md, and outputs/CONSOLIDATED_RESULTS.md before anything else.
This session is ZERO API SPEND — every task below runs locally against committed data. No
live calls for any reason. Unattended rules from the last session apply: judgment calls are
made in favor of data validity and recorded in STATUS.md.

PART A — TWO ANALYSES THE REPORT STILL NEEDS

1. Competing-risks sensitivity (T28). Refusal and exit compete for the same conversations,
   so raw refusal proportions are not comparable across conditions whose exit rates differ.
   For every model x category x condition cell that has any code (a), compute refusal two
   ways side by side: over all conversations (the current definition) and over non-exit
   conversations only (code a removed from the denominator). Report both denominators' n.
   Commit as outputs/T28_competing_risks.csv. Then answer in one committed paragraph:
   does the RQ2 claim that refusal is "biased toward the least agentic tool" survive on the
   non-exit denominator, or does exit substitution account for the exit_schema gap in
   llama4_maverick? Do not change the primary DV definition anywhere — this is a declared
   sensitivity view, recorded in a section 10 entry.

2. Within-category type decomposition (T29). For every model with nonzero refusal or exit
   in categories C or D, break the cell down by task type (C: F-to-C, alphabetical, roman;
   D: crossword, metaphor, acronym) per condition, with per-type n stated. Commit as
   outputs/T29_type_decomposition.csv. Answer in a committed paragraph: is gemini25_flash's
   C effect roman-driven, and does that vindicate the 2026-08-15T20:45Z diagnostic verdict
   that the n=2-per-cell typearm could not test? Update the reconciliation section of
   STIMULUS_PROVENANCE.md accordingly rather than leaving it stale. Same question for
   gemma3_27b's C and D effects and qwen3_235b's category-A exits (A has no types; skip it)
   — wherever a category-level claim could actually be a type-level claim, say which.

3. Ladder bookkeeping. State explicitly in a STATUS entry which two llama4_maverick
   160-item cells were truncation-suppressed, and how the code (c) capability check
   resolved at n=160 for llama4 given the suppression — scored, or capability-limited. If
   the report's llama4 ladder sentences rest partly on suppressed cells, amend them.

4. Update outputs/CONSOLIDATED_RESULTS.md wherever T28 or T29 changes a statement — at
   minimum the RQ2 "least agentic tool" sentence and the gemini task-type sentences. Keep
   every number cited to a committed file. Update BOOKMARKS.md: B2 resolved (dose tested;
   refuted for gpt_oss refusal, produced the qwen dose-response), B3 resolved or reopened
   per T29's roman answer, B1 updated with the split code-c verdict.

PART B — FIGURES

Create figures/ governed by one script, src/make_figures.py, that deletes and rebuilds the
entire directory from committed outputs/ files on every run. No figure is ever hand-edited;
stale figures are impossible by construction. Each PNG embeds the SHA256 of its source
CSV(s) in its metadata, and figures/MANIFEST.md lists every figure with its claim, sources,
and grades. Matplotlib, colorblind-safe palette, one figure one claim, every figure carries
per-cell n and evidentiary grade on the figure itself, Wilson intervals wherever a
proportion is drawn. A caption text file per figure states the claim in one sentence, then
sources. F2 stays vacated — do not reuse the name.

- F1 (main result): refusal by condition for the four affected models (llama4, gemini_flash,
  gemma3, qwen3), confirmatory grade only, drawn as the two overlapping comparisons — the
  tool-identity set and the presentation set side by side with exit_schema visually marked
  as the shared hinge — faceted by category where the effect lives. If T28 changes the
  llama4 picture, F1 shows the non-exit-denominator view alongside or the caption says why
  not.
- F3 (dose-response): qwen3_235b exit rate versus requested items (20/40/160) for
  exit_schema and exit_both, with none-condition completion fraction plotted as the
  capability reference. Probe grade and per-cell n prominent. gpt_oss's two 160-item exits
  as annotated points, not a line.
- F4 (outcome substitution): stacked composition — comply / verbal refusal split b,c,d /
  exit — by condition for llama4_maverick and qwen3_235b at confirmatory grade. This is the
  competing-risks point made visual.
- F5 (channel dissociation): qwen3_235b, exit_schema versus exit_prose versus exit_both:
  exit rate and verbal refusal rate side by side, categories A and D. Caption carries the
  T18 distinct-text caveat verbatim.
- F6 (cell census map): model x category x size tiles colored by grade with n printed —
  the orientation figure for us, likely appendix in the manuscript.
- Ren et al. category ratings (A −1.17, B −0.33) appear only as text annotations on A/B
  labels, never as a plotted continuous axis — no per-task, per-model preference measure
  exists and a drawn axis would imply one (BOOKMARKS B6).
- F7 (orientation grid): model x category grid of stacked composition bars (comply / verbal refusal split b,c,d / exit), one bar PER CONDITION within each panel — never pooled across conditions, since the baseline-vs-tool contrast is the finding. Confirmatory-grade models only in the main version; a second all-models version including screen-grade panels, each panel labeled with its grade and per-cell n, goes to the appendix set.

PART C — HAND-LABEL TOOLING

Build a single-file local labeling interface (CLI or self-contained HTML, no network)
that reads derived/handlabel_sample.jsonl, presents each response condition-stripped,
accepts labels a/b/c/d/none plus an optional note, is resumable mid-session, and writes
derived/handlabels_cole.jsonl. Add src/compute_human_kappa.py that produces
outputs/T7_human_kappa.csv from those labels versus the primary classifier, with the
per-code confusion matrix, and prints the METHODOLOGY section 8 consequence if kappa is
below 0.70. Estimate and print expected labeling time at 15 seconds per item.

PART D — CLOSE OUT

STATUS entry covering every part, updated commit per part, tree clean. If any T28/T29
recomputation contradicts a committed number rather than refining its interpretation, stop
and report — do not fix committed history.