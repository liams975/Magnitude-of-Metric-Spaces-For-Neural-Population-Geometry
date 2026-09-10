# Project context — Decoder Drift Sprint

Single source of truth for what this repo is doing, why, and where it currently stands.
Read this file first in any new session before touching code.

## The question

**Before (original framing, now superseded):** Magnitude of Metric Spaces for Neural
Population Geometry — what does the magnitude function of a neural population point
cloud reveal about the structure of the population code? Purely descriptive, no
dependent variable, no way to be wrong.

**After (current framing, redirected 6 Sept 2026):** Does a geometric invariant of the
neural population, computed on **unlabeled** data from a new recording day, predict how
badly a fixed intracortical decoder will degrade on that day? Magnitude is the novel
entrant in a benchmark of unsupervised drift predictors.

The magnitude machinery itself didn't change. What changed is that it now has a
dependent variable (ΔR² of a frozen decoder), a control arm (seven baseline predictors),
and a hard constraint on its inputs (no behavioural labels allowed).

**The paper is one table:** 8 predictors (7 baselines + magnitude) × 3 datasets (M1, M2,
H1), each cell a Spearman ρ between an unlabeled-data predictor and per-session ΔR².
Everything after week 6 is analysis and prose written on top of a table that already
exists by then.

|                     | M1 | M2 | H1 |
|---------------------|----|----|----|
| Linear CKA          | ρ  | ρ  | ρ  |
| Procrustes          | ρ  | ρ  | ρ  |
| Participation ratio | ρ  | ρ  | ρ  |
| Subspace angle       | ρ  | ρ  | ρ  |
| Mean rate shift      | ρ  | ρ  | ρ  |
| Channel-wise KS      | ρ  | ρ  | ρ  |
| Shesha               | ρ  | ρ  | ρ  |
| **Magnitude family** | ρ  | ρ  | ρ  |

Why this framing protects the ship date: the old version only succeeds if magnitude
wins, which couples a fixed deadline to an open research question. Now, if magnitude
wins it's the headline; if it loses, the paper is still a rigorous negative result plus
the first systematic head-to-head of these predictors on FALCON — same code, same
figures, same date, different title.

## Ship date and operating rules

- **Anchor:** arXiv, Monday 14 December 2026.
- **Budget:** 15–20 h/week, solo, ~240 h total, public data only, laptop-scale.
- **Gate 1 — Sunday 18 Oct:** PASS if a magnitude-family predictor reaches Spearman
  |ρ| ≥ 0.5 against per-session ΔR² on at least one dataset, ranks above the best
  baseline, and the margin survives a session-level permutation test at p < 0.05. Fail
  does **not** mean switch projects — retitle to the benchmark/negative-result framing,
  everything else carries over unchanged.
- **Gate 2 — Sunday 15 Nov: experiment freeze.** No new analysis after this date,
  regardless of how good an idea looks. Non-negotiable.
- **Weekly rhythm:** Monday 08:00 plan / Friday 17:00 review. Deliverables are binary —
  landed or not, no partial credit. Two misses in a row triggers cutting scope (a
  dataset or an analysis), never moving the date.
- Full 14-week breakdown, risk register, and rationale for every decision live in the
  published planning artifact (Decoder Drift Sprint) — this file is the durable summary;
  that artifact is the interactive tracker.

## What carries over from the original magnitude project

1. **The magnitude machinery, unchanged.** For finite metric space X = {x₁…xₙ}: form
   Z(t)ᵢⱼ = e^(−t·d(xᵢ,xⱼ)), solve Z(t)w = 1, take |tX| = Σwᵢ. The object of study is the
   function t ↦ |tX|, not a single number.
2. **Conditioning know-how.** Z(t) → all-ones matrix as t → 0, so small-t is
   near-singular and will silently return plausible garbage. This is a known failure
   mode from prior certified-computation work — handle with solver choice,
   regularisation, and a documented usable-t range. Known in advance, so week 4 is a
   one-week task, not a debugging spiral.
3. **Closed-form validation suite** (becomes the week-4 unit tests):
   - 2 points at distance d → 2/(1+e^(−td))
   - n points at mutual distance d → n/(1+(n−1)e^(−td))
   - segment [0,ℓ] → 1 + tℓ/2
   - multiplicativity on ℓ¹ products
   - limits: |tX| → 1 as t → 0, → n as t → ∞
4. **Secondary summaries.** Magnitude dimension (log–log slope profile, per Andreeva et
   al.) and area under the magnitude curve — both survive as derived features.
5. **The point-cloud construction question** survives as the first modelling decision,
   but every detail of the answer changes (see below).
6. **Related work**, close to verbatim: Leinster; Meckes on positive-definiteness of
   e^(−td) on Euclidean subsets (why the weighting always exists here); Andreeva et al.
   on magnitude and generalisation (arXiv 2305.05611); Limbeck et al. NeurIPS 2024 on
   magnitude and diversity.
7. **Operating constraints unchanged:** public data only, laptop-scale, solo, arXiv-first.

## What was dropped

1. The certified-computation programme (interval arithmetic, Galerkin/FEM bounds,
   dual measure-theoretic bounds, two-sided brackets) — magnitude is now just a
   numerically computed feature; the permutation test absorbs its error.
2. Continuum magnitude (Euclidean-ball weight measures, Bessel potential operator,
   unit-disk open problem) — irrelevant, only finite point clouds are ever computed.
3. The purely descriptive aim — unfalsifiable, not interesting to a reviewer.
4. The pure-mathematics contribution — there is no theorem in this paper anymore; the
   contribution is empirical and methodological.
5. Trial-structured, condition-averaged point clouds — banned by the unlabeled axiom.
6. Applied-maths / geometry venues — this is now an ML / computational neuroscience paper.
7. The coauthor. Solo project.

## The three structural changes

- **Descriptive → predictive.** Unit of analysis is now a (session, fixed decoder) pair
  with a measured ΔR². Every claim is a correlation against a pre-specified outcome.
- **Single method → benchmark with an entrant.** Seven baselines (linear CKA,
  Procrustes, participation ratio, PCA subspace angles, mean rate shift, channel-wise
  KS, Shesha) are implemented in week 3, *before* magnitude in week 4 — deliberately
  inverting the risk. Magnitude failing no longer kills the paper.
- **The unlabeled axiom.** Every predictor must be computable from the new day's neural
  data with **no behavioural labels**. If you have labels, you'd just measure R²
  directly — no predictor needed. This is a real constraint, not framing: it rules out
  condition-averaging, trial alignment, anything keyed to the behavioural target. It's
  also what makes the output a monitoring tool rather than a correlation study.

Consequence: the point cloud is unlabeled binned spike counts from a held-out session —
rows = time bins, coordinates = channels, subsampled to a fixed n for cross-session
comparability. **Open confound to settle before week 4:** whether to normalise each
session's cloud to unit scale. Unnormalised, magnitude at fixed t partly re-measures
overall firing-rate change (already baseline #5 — mean rate shift). The paper must
answer "is magnitude just a rate shift in disguise?" — normalisation is where that
answer lives. Report both ways.

## The competitive landscape (why urgency, why new baselines)

- **"Geometric Stability of Neural Population Codes"** (arXiv 2606.29655, June 2026) —
  applies a split-half RDM rank-correlation measure ("Shesha") to electrophysiology;
  geometric stability dissociates from centroid drift and predicts neural-behavioural
  coupling. They explicitly state cross-session stability and decoder generalization
  are **not investigated** — that gap is this paper. Cite it. **Shesha is now a
  mandatory baseline** — beating CKA/Procrustes alone won't satisfy a reviewer.
- **"The Geometric Canary"** (arXiv 2604.17698) — companion paper, shows this class of
  measure beating CKA 2× on drift sensitivity and beating Procrustes on false-alarm
  rate, but in language-model representations, using rank correlation, not magnitude.
  Cite it too.
- NeurIPS 2026 workshop routes (BrainBodyFM, NeurReps) are both closed as of 6–8 Sept
  2026 — not reachable from a standing start. December arXiv is the clean primary
  target. Downstream: COSYNE 2027 (submissions open "this fall", watch in week 10),
  ICLR 2027 workshops (~Feb), NeurIPS 2027 with a preprint already in hand.

## Datasets and reproduction targets

FALCON benchmark (`snel-repo/falcon-challenge`, `pip install falcon-challenge`), data on
DANDI, no application required. Using three of five available datasets — skipping H2
(handwriting→text, WER metric) and B1 (birdsong→spectrogram, MSE) because M1/M2/H1
share an R² target (one pipeline covers all three) and the hour budget has no room for
metric-specific pipelines.

| Dandiset | Task | Covariate | Channels |
|---|---|---|---|
| `000941` | M1, monkey reach-grasp | EMG, 16 muscles | 64 (A) / 96 (B) |
| `000953` | M2, monkey finger | 2-D finger velocity | 96 |
| `000954` | H1, human hand | 7-D hand velocity | 172 |

All bin at **20 ms**. EvalAI leaderboard (challenge 2319) accepts submissions
indefinitely — no deadline, submit something by week 9.

**Corrected Wiener-filter reproduction targets** (the earlier "≈0.28 held-out drop"
figure in the original plan doc was wrong — use these):

| Dataset | Held-in R² | Held-out R² |
|---|---|---|
| M1-A (64 ch) | 0.54 | 0.34 |
| M2 (96 ch) | 0.27 | 0.06 |
| H1 (172 ch) | 0.24 | 0.16 |

M2's held-out R² sits near the floor and H1's band is narrow — both compress the
variance of ΔR², the quantity every correlation is taken against. **M1 is where the
design has the most room**, and is the week-1 reproduction target: held-in ≈ 0.54,
held-out ≈ 0.34, within ≈ ±0.05.

⚠️ **Verified 9 Sept 2026:** the held-out figures above come from a baseline that
re-normalises inputs per session using that day's own unlabeled statistics. A decoder
that is frozen in the strict sense this project requires does *much* worse on held-out
data. Don't treat 0.34 as a target our own decoder should hit — see Current status →
"Held-out reproduction gap".

## Data access nuance (resolved favourably)

Earlier risk: held-out session labels might be locked behind EvalAI, making per-session
ΔR² uncomputable locally. **Resolved: they are not.** `held_out_calib` is on disk with
labels. What's behind EvalAI is only the full eval split. So per-session ΔR² is
computable locally, but from deliberately little labeled data per held-out session
(the split exists for few-shot recalibration) — noisy, not impossible. Mitigation
(decided): run two ΔR² designs in parallel —
- **(a) Headline design** — train on pooled held-in, evaluate on each `held_out_calib`
  session. The real monitoring scenario. Noisier per-session R².
- **(b) Development design** — train on the earliest held-in session, evaluate on every
  later held-in session. Tighter estimates, shorter elapsed-time span. Use as the
  working harness while building weeks 3–5.

Agreement between (a) and (b) is a free robustness paragraph in week 7.

## Planned repo layout (create in week 1, don't retrofit later)

```
├── data/<id>/<id>/         # gitignored — dandi nests an extra <id>/ level
├── src/
│   ├── io.py               # session discovery, loading, caching, manifest
│   ├── decoder.py          # the frozen Wiener filter + per-session scoring
│   └── figures.py          # CLI orchestrator: manifest -> fit -> score -> figure
├── cache/                  # gitignored — .npz per session, .joblib frozen model
├── results/                # sessions_manifest.csv, m1_session_r2.csv (committed)
├── figures/
├── notes/                  # redirect-memo.md, m1_data_demo_executed.ipynb
├── requirements.lock
└── Makefile                # `make figure1` = the one command
```
`data/` and `cache/` are gitignored; `results/` (the actual predictor/target CSVs) is
committed — it's small and it's the evidence base the whole paper regresses on. The
work happens in this repo directly, not the separate `~/research/drift` dir the memo
sketched. There is no `src/evaluate.py`: per-session R² is a method on `WienerFilter`,
where it belongs.

## Traps (read before writing decoder/preprocessing code)

1. **Any per-session normalisation is secret recalibration.** If preprocessing z-scores
   neural data using each session's own mean/variance, the decoder has been quietly
   recalibrated to every session — the degradation curve flattens, ΔR² loses variance,
   and in week 5 it looks like nothing predicts anything. **All normalisation
   statistics must be fit on held-in training data and frozen with the model.** Most
   likely way to silently kill this project; wouldn't announce itself until week 5.
2. **Don't build on the FALCON submission harness** (reset/observe/predict/on_done) for
   analysis code — it's shaped for streaming leaderboard scoring, not "freeze a
   decoder, point it at an arbitrary session, get one number back." Reimplement the
   Wiener filter directly.
3. **Don't clean the data creatively.** Use FALCON's own preprocessing. Inventing custom
   spike filtering means week-3 baselines measure your choices, not the data, and no
   reviewer can compare your CKA number to anyone else's.
4. **Record n_bins per session now.** Magnitude requires an n×n solve — O(n³). A
   50,000-bin session isn't solved directly; a subsampling policy is needed in week 4.
   Knowing the distribution of n now means designing that policy deliberately.
5. `eval_mask` is not decorative — R² is scored on masked timepoints only.
6. `r2_score(..., multioutput='variance_weighted')` — **not** sklearn's default
   (`uniform_average`), which gives a different, wrong number vs. the FALCON metric.

## Current status — as of 9 Sept 2026 (day 3 of week 1, 7–13 Sept)

**Week 1 is done, ahead of schedule.** Everything below actually ran against real data
in this repo — nothing here is aspirational.

- Repo layout built out: `src/`, `data/` (gitignored), `cache/` (gitignored),
  `results/`, `figures/`, `notes/`, plus `.gitignore`, `Makefile`, `requirements.lock`.
- `.venv` created (Python 3.14); `falcon-challenge`, `dandi`, `pynwb`, `scikit-learn`,
  `pandas`, `matplotlib`, `seaborn`, `jupyter`/`nbconvert` installed and pinned in
  `requirements.lock`.
- **M1 (`000941`) and M2 (`000953`) are both fully downloaded** — not just started.
  M1: 311.8 MB, 11 sessions. M2: 15.9 GB, 21 files across 12 unique session-days
  (some days have two runs). Both land under `data/<id>/<id>/...` — `dandi download -o
  data/<id> <url>` nests an extra `<id>/` level, `src/io.py`/`figures.py` account for
  it. H1 correctly left for week 2, per plan.
  **Note the DANDI `assetsSummary.numberOfBytes` field is stale/wrong for 000953**
  (reports 37 MB) — always trust the actual `assets/` listing, not that summary field.
- `notes/redirect-memo.md` written and present (the actual week-1-task-1 deliverable;
  this `CONTEXT.md` is the broader, longer-lived companion doc, not a replacement for it).
- **The official `data_demos/m1.ipynb` was run end to end, unmodified**, from a clone
  of `snel-repo/falcon-challenge` (that notebook isn't shipped in the `falcon-challenge`
  PyPI package — only in the GitHub repo). Executed copy saved at
  `notes/m1_data_demo_executed.ipynb`. Its own from-scratch decoder (single-day
  training, exponential smoothing, per-session z-scoring) got held-out R² = 0.48, 0.28,
  0.18 (mean ≈ 0.31) on the three held-out days — closely reproducing the paper's 0.34,
  and confirming data loading / `eval_mask` / covariate handling are all correct.
- **`src/io.py`, `src/decoder.py`, `src/figures.py` written** (no separate
  `src/evaluate.py` — per-session scoring is one method on `WienerFilter`
  (`decoder.py`); a whole extra file for it would've been pure indirection).
  `python3 -m src.figures --dataset m1 --out figures/fig1_degradation_m1.png`
  (equivalently `make figure1`) runs the entire pipeline — manifest, frozen decoder,
  per-session R², figure — from a clean checkout, verified by actually deleting
  `cache/`+`results/`+the figure and rerunning. Deterministic: identical numbers both
  runs.
- **Our own frozen Wiener filter** (ridge, 10 lags/200 ms, sqrt-transformed spikes,
  channel-wise normalisation stats fit once on pooled held-in and frozen, alpha
  frozen via CV on held-in only — zero adaptation of any kind at eval time) trained on
  the 4 M1 held-in-calib sessions pooled. Held-in R² = 0.57–0.59 (close to the 0.54
  target). **Held-out R² is strongly negative: −0.61, −0.95, −0.61** — nowhere near
  the published 0.34. `figures/fig1_degradation_m1.png` shows this honestly (had to
  fix the plot's y-axis, which was hardcoded to [0,1] and was silently clipping the
  held-out points off the chart entirely).
- **This gap is diagnosed, not a bug — see "Held-out reproduction gap" below.** It's a
  real, load-bearing finding, not a rounding error.
- `falcon.ipynb`'s broken cell (shell commands with no `!` prefix, so it threw a
  `SyntaxError` and had never run) is fixed and reflects the actual, already-completed
  download.
- `Initial.ipynb` untouched — still has the pre-redirect `defect(D, p)` leftover
  function, unrelated to this week. Left alone; not a week-1 concern.
- Nothing has been committed to git yet — all of the above is in the working tree,
  awaiting review.

### Held-out reproduction gap (important, and unresolved by design)

Our fully-frozen decoder gets M1 held-out R² of about −0.7 on average, not the
published +0.34. Root cause, confirmed two independent ways (FALCON's own
`decoder_demos/sklearn_decoder.py`, and by rerunning our decoder with a per-session
normalisation swapped in): **FALCON's own reference baseline re-normalises input
neural features per session, using that session's own unlabeled statistics**, even
though its regression weights stay frozen. Swapping that same trick into our decoder
recovers held-out R² of 0.37–0.50 (mean ≈ 0.44) — squarely in the published range,
confirming the pipeline itself (data loading, `eval_mask`, `variance_weighted` R²,
session bookkeeping) is correct. The −0.7 vs +0.34 gap is a genuine protocol
difference, not a defect.

We kept the fully-frozen version as what `src/decoder.py` actually ships, because:
- The redirect memo's Trap #1 explicitly warns that any per-session normalisation is
  "secret recalibration" that flattens the degradation curve and destroys the ΔR²
  variance the whole benchmark regresses on — and empirically, per-session
  normalisation *did* compress held-in vs. held-out from a 1.2-point R² gap down to
  about 0.15, i.e. it measurably erases the signal this project exists to predict.
- Week 2's own task list commits to "zero-shot, fixed decoder, **no calibration**" as
  the permanent protocol — our decoder already matches that.

Net effect: **the reproduction check target in the plan (±0.05 of 0.34) will not be
hit under this project's own intended protocol, and that's expected, not a bug to
chase.** A −0.7 held-out R² under a genuinely fixed decoder is, if anything, a more
dramatic and more publishable motivating result than +0.34 — it's stronger evidence
that decoder drift is severe and worth predicting. This should be treated as settled
unless revisited deliberately; full detail and numbers in
`notes/redirect-memo.md`'s addendum.

### Held-out session counts (the number week 2 needed)

Both M1 and M2 are under the "~8" threshold in the risk register, so its week-2
mitigation is already triggered, not just worth checking:
- **M1: 3 held-out sessions** (ses-20121004, ses-20121017, ses-20121024).
- **M2: 4 unique held-out days, 6 files** (2020-10-30 ×2 runs, 2020-11-18, 2020-11-19,
  2020-11-24 ×2 runs).

Week 2 should start from "decide how this design gets statistical power" (pooling
across datasets, sub-block splitting, bootstrap CIs) rather than treating that as an
open question to check.

## Week 1 — definition of done (7–13 Sept 2026, 16 h budget)

Deliverable: a plot of R² per session on M1 — held-in and held-out marked, against days
elapsed — from your own code, in the git repo. It's a correctness proof of four things
at once: data loading, the decoder, the R² definition, and session bookkeeping. Not
touching magnitude (week 4), not using M2/H1 (week 2), not optimizing the decoder, not
writing paper prose.

- [x] Redirect memo written and committed (`notes/redirect-memo.md`)
- [x] M1 and M2 downloaded from DANDI; `data_demos` M1 notebook run end to end, unmodified
- [x] `results/sessions_manifest.csv` — every session with split, date, n bins, n units,
      labeled minutes
- [x] Own Wiener filter (ridge on ~10 lags of 20 ms bins) trained on pooled held-in M1,
      hyperparameters frozen
- [x] Per-session R² computed for all held-in and all held-out M1 sessions
- [x] `figures/fig1_degradation_m1.png` regenerates from raw data with one command, from
      a clean checkout

All six landed. The one open item is a judgment call, not a task: whether the
held-out reproduction gap above needs a second look before week 2 builds on top of
this decoder.

## Reference links

- FALCON benchmark: https://snel-repo.github.io/falcon/
- Starter code: https://github.com/snel-repo/falcon-challenge
- EvalAI leaderboard: https://eval.ai/web/challenges/challenge-page/2319/overview
- FALCON NeurIPS 2024 paper (Wiener-filter numbers source)
- DANDI 000941 (M1) · 000953 (M2) · 000954 (H1)
- Geometric Stability of Neural Population Codes — arXiv 2606.29655
- The Geometric Canary — arXiv 2604.17698
- Magnitude and Generalisation in Neural Networks (Andreeva et al.) — arXiv 2305.05611
- COSYNE abstract submission — https://www.cosyne.org/abstracts-submission
- arXiv endorsement policy — https://arxiv.org/help/endorsement
