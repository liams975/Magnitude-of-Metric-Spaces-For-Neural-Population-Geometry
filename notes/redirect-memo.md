# Redirect memo — what carries over from the magnitude project

Week 1 deliverable · 7 September 2026

## The question, before and after

**Before.** Magnitude of Metric Spaces for Neural Population Geometry — what does the
magnitude function of a neural population point cloud reveal about the structure of the
population code?

**After.** Does a geometric invariant of the neural population, computed on unlabeled
data from a new recording day, predict how badly a fixed intracortical decoder will
degrade on that day? Magnitude is the novel entrant in a benchmark of unsupervised
drift predictors.

The invariant is unchanged. What changed is that it now has a dependent variable, a
control arm, and a constraint on its inputs.

## Imported — carries over intact

1. **The magnitude machinery itself.** For a finite metric space X = {x₁…xₙ}, form
   Z(t)ᵢⱼ = e^(−t·d(xᵢ,xⱼ)), solve Z(t)w = 1, take |tX| = Σwᵢ. The object of study is the
   function t ↦ |tX|, not a single number. Same definition, same solver, same code.
2. **Conditioning know-how** from the certified-computation work. Z(t) → the all-ones
   matrix as t → 0, so the small-t regime is near-singular and will silently return
   plausible garbage. Knowing this in advance is what makes week 4 a one-week task
   instead of a three-week debugging spiral. Carries over as: solver choice,
   regularisation policy, and a documented usable-t range.
3. **The closed-form validation suite.** Two points at distance d → 2/(1+e^(−td)). n
   points at mutual distance d → n/(1+(n−1)e^(−td)). Segment [0,ℓ] → 1 + tℓ/2.
   Multiplicativity on ℓ¹ products. Limits: |tX| → 1 as t → 0, → n as t → ∞. These
   become the unit tests the week-4 deliverable is defined by.
4. **Secondary summaries.** Magnitude dimension (the log–log slope profile, following
   Andreeva et al.) and area under the magnitude curve. Both survive as derived
   features.
5. **The point-cloud construction question.** Turning a recording session into a
   finite metric space was always the first modelling decision. It survives — but every
   detail of the answer changes (see below).
6. **Related work.** Leinster; Meckes on positive-definiteness of e^(−td) on Euclidean
   subsets (why the weighting always exists here); Andreeva et al. on magnitude and
   generalisation (arXiv 2305.05611); Limbeck et al. NeurIPS 2024 on magnitude and
   diversity. This block of the paper is reusable close to verbatim.
7. **Operating constraints.** Public data only, laptop-scale, solo, arXiv-first.

## Dropped

1. The certified-computation programme — interval arithmetic, primal Galerkin/FEM
   upper bounds, dual measure-theoretic lower bounds, two-sided brackets. Magnitude is
   now a numerically computed feature; the permutation test absorbs its error. Rigorous
   error control buys nothing here.
2. Continuum magnitude — weight measures for Euclidean balls, the half-integer-order
   Bessel potential operator, its nonlocality in even dimensions, the unit-disk open
   problem. Irrelevant: we only ever compute magnitude of finite point clouds, where
   the weighting is a linear solve.
3. The descriptive aim. "Magnitude is an informative descriptor of population
   geometry" is a claim with no way to be wrong, and therefore no way to be interesting
   to a reviewer.
4. The pure-mathematics contribution. There is no theorem in this paper. The
   contribution is empirical and methodological.
5. Trial-structured, condition-averaged point clouds. Banned by the unlabeled
   constraint.
6. Applied-maths and geometry venues. The paper is now ML / computational
   neuroscience.
7. The coauthor. Solo.

## The three structural changes

- **Descriptive → predictive.** The unit of analysis is no longer "a population." It
  is a (session, fixed decoder) pair with a measured ΔR². Every claim is now a
  correlation against an outcome that was not chosen after the fact.
- **Single method → benchmark with an entrant.** Seven baselines — linear CKA,
  Procrustes, participation ratio, PCA subspace angles, mean rate shift, channel-wise
  KS, and Shesha — are implemented in week 3, deliberately before magnitude in week 4.
  This inverts the project's risk: previously magnitude failing meant no paper; now it
  means a negative result inside a benchmark that is itself the contribution.
- **The unlabeled axiom.** Every predictor must be computable from the new day's
  neural data with no behavioural labels. If you have the labels, you measure R²
  directly and need no predictor at all. This is a real mathematical constraint, not a
  framing device: it rules out condition-averaging, trial alignment, and anything keyed
  to the behavioural target. It is also what makes the output a monitoring tool rather
  than a correlation study.

Consequently the point cloud is now: unlabeled binned spike counts from a held-out
session, points = time bins, coordinates = channels, subsampled to a fixed n for
cross-session comparability. Open confound to settle before week 4: whether to
normalise each session's cloud to unit scale. If not normalised, magnitude at fixed t
partly re-measures overall firing-rate change — which is already baseline #5. The
paper must answer "is magnitude just a rate shift in disguise?" and normalisation is
where that answer lives.

## Section-by-section

| Section | Fate |
|---|---|
| Title, abstract | Rewritten |
| Introduction | Rewritten — decoder drift and recalibration cost, not population geometry |
| Related work | ~70% reusable; add FALCON/drift, CKA/Procrustes/RSA, both Shesha papers |
| Methods — magnitude | Survives intact |
| Methods — point cloud | Structure survives, every detail changes |
| Methods — protocol, ΔR², baselines, statistics | All new |
| Results | Nothing survives |
| Discussion | New — framed around a monitoring tool |

## Correction to the plan document

The week-1 reproduction target stated as "≈0.28 R² held-out drop on M1" does not match
the FALCON paper. The reported Wiener-filter figures are:

| Dataset | Held-in R² | Held-out R² |
|---|---|---|
| M1-A (64 ch) | 0.54 | 0.34 |
| M2 (96 ch) | 0.27 | 0.06 |
| H1 (172 ch) | 0.24 | 0.16 |

So the week-1 check is held-in ≈ 0.54, held-out ≈ 0.34 on M1-A, a drop of ≈0.20. M1 has
A and B subsets (64 and 96 channels) — this project uses A.

Second-order consequence for week 2: M2's held-out R² sits near the floor and H1's
band is narrow. Both compress the variance of ΔR², which is the quantity every
correlation in this paper is taken against. M1 is where the design has the most room.

**Post-execution addendum (9 Sept 2026):** the ≈0.34 figure above was reproduced by
FALCON's *own* reference decoder, which — per its published `sklearn_decoder.py` —
z-scores each session's input neural features using **that session's own unlabeled
statistics** before decoding, even though its regression weights stay frozen. Our
decoder, built per this memo's explicit instruction ("no calibration," every
normalisation statistic frozen on held-in data), does not do this, and lands far
below the target on held-out data as a result. See `CONTEXT.md` → Current status for
the full finding and the reasoning for keeping the fully-frozen design anyway.
