"""A frozen Wiener filter: ridge regression on lagged, sqrt-transformed spike counts.

Deliberately not built on falcon_challenge's submission harness (reset/observe/predict),
which is shaped for streaming leaderboard scoring. This gives the opposite shape: fit
once on pooled held-in data, then point it at an arbitrary session's arrays and get one
R^2 back.

Trap this file exists to avoid: any normalisation statistic that is fit per-session is
secret decoder recalibration, and will flatten the degradation curve this whole project
measures against. So every statistic below (channel mean/std, ridge alpha, n_lags) is
fit ONCE on pooled held-in training data and then frozen into the WienerFilter object.
"""
from dataclasses import dataclass, field

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

N_LAGS = 10          # 10 lags * 20ms bins = 200ms of history
ALPHA_CANDIDATES = [1.0, 10.0, 30.0, 100.0, 300.0, 1000.0]


def sqrt_transform(neural: np.ndarray) -> np.ndarray:
    """Variance-stabilising transform. Deterministic, no per-session fitting -> safe."""
    return np.sqrt(neural.astype(np.float64))


def make_lagged(x: np.ndarray, n_lags: int = N_LAGS) -> np.ndarray:
    """(T, C) -> (T, C*n_lags); row t = channel values from bins t-n_lags+1 .. t."""
    T, C = x.shape
    out = np.zeros((T, C * n_lags), dtype=np.float64)
    for i in range(n_lags):
        out[i:, i * C:(i + 1) * C] = x[: T - i]
    return out


def valid_lag_mask(trial_change: np.ndarray, n_lags: int = N_LAGS) -> np.ndarray:
    """False for the first n_lags bins overall, and the first n_lags bins after every
    trial change -- those lag windows would straddle a trial boundary and mix
    unrelated data."""
    T = trial_change.shape[0]
    mask = np.ones(T, dtype=bool)
    mask[:n_lags] = False
    change_idx = np.flatnonzero(trial_change)
    for idx in change_idx:
        mask[idx: idx + n_lags] = False
    return mask


@dataclass
class WienerFilter:
    n_lags: int = N_LAGS
    alpha: float | None = None
    norm_mean: np.ndarray | None = None
    norm_std: np.ndarray | None = None
    model: Ridge | None = None
    train_session_ids: list = field(default_factory=list)

    def _normalize(self, sqrt_neural: np.ndarray) -> np.ndarray:
        return (sqrt_neural - self.norm_mean) / self.norm_std

    def features(self, neural: np.ndarray) -> np.ndarray:
        z = self._normalize(sqrt_transform(neural))
        return make_lagged(z, self.n_lags)

    def fit(self, pooled_neural: np.ndarray, pooled_cov: np.ndarray, pooled_trial_change: np.ndarray,
            pooled_eval_mask: np.ndarray, session_ids: list[str]):
        """Fit on pooled held-in data only. Freezes norm stats and alpha."""
        self.train_session_ids = list(session_ids)

        sqrt_neural = sqrt_transform(pooled_neural)
        self.norm_mean = sqrt_neural.mean(axis=0)
        self.norm_std = sqrt_neural.std(axis=0)
        self.norm_std[self.norm_std == 0] = 1.0

        mask = pooled_eval_mask & valid_lag_mask(pooled_trial_change, self.n_lags)
        X = self.features(pooled_neural)[mask]
        Y = pooled_cov[mask]

        # Freeze alpha by cross-validation on held-in data only, before ever touching
        # a held-out session -- picked once, never re-tuned per session.
        split = int(0.8 * len(X))
        X_tr, X_val = X[:split], X[split:]
        Y_tr, Y_val = Y[:split], Y[split:]
        best_alpha, best_score = ALPHA_CANDIDATES[0], -np.inf
        for a in ALPHA_CANDIDATES:
            m = Ridge(alpha=a).fit(X_tr, Y_tr)
            score = r2_score(Y_val, m.predict(X_val), multioutput="variance_weighted")
            if score > best_score:
                best_alpha, best_score = a, score
        self.alpha = best_alpha

        # Refit on ALL pooled held-in data with the frozen alpha.
        self.model = Ridge(alpha=self.alpha).fit(X, Y)
        return self

    def predict(self, neural: np.ndarray) -> np.ndarray:
        return self.model.predict(self.features(neural))

    def score_session(self, neural: np.ndarray, cov: np.ndarray, trial_change: np.ndarray,
                       eval_mask: np.ndarray) -> tuple[float, int]:
        """Returns (R^2, n_eval_bins_used) for one session, under the frozen model."""
        mask = eval_mask & valid_lag_mask(trial_change, self.n_lags)
        pred = self.predict(neural)
        r2 = r2_score(cov[mask], pred[mask], multioutput="variance_weighted")
        return float(r2), int(mask.sum())

    def save(self, path):
        import joblib
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        import joblib
        return joblib.load(path)
