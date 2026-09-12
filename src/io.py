
from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pandas as pd

from falcon_challenge.dataloaders import load_nwb
from falcon_challenge.config import FalconTask

BIN_SIZE_S = 0.02

TASK_BY_DATASET = {
    "m1": FalconTask.m1,
    "m2": FalconTask.m2,
    "h1": FalconTask.h1,
}

SPLIT_DIR_RE = re.compile(r"^sub-\w+?-(held-in-calib|held-in-minival|held-out-calib|minival)$")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{8})")


@dataclass
class Session:
    path: Path
    dataset: str          # "m1" | "m2" | "h1"
    split: str             # "held-in-calib" | "held-in-minival" | "held-out-calib"
    session_id: str        # e.g. "ses-20120924" or "ses-2020-10-27-Run1"
    date: pd.Timestamp

    @property
    def stem(self) -> str:
        return self.path.stem


def _parse_date(session_id: str) -> pd.Timestamp:
    m = DATE_RE.search(session_id)
    if not m:
        raise ValueError(f"Could not parse a date out of session id {session_id!r}")
    raw = m.group(1)
    if len(raw) == 8:  # YYYYMMDD
        return pd.to_datetime(raw, format="%Y%m%d")
    return pd.to_datetime(raw, format="%Y-%m-%d")


def discover_sessions(dataset_dir: Path, dataset: str) -> list[Session]:
    """Walk a downloaded dandiset directory and return every session, split included."""
    sessions = []
    for split_dir in sorted(dataset_dir.glob("sub-*")):
        if not split_dir.is_dir():
            continue
        m = SPLIT_DIR_RE.match(split_dir.name)
        split = m.group(1) if m else split_dir.name
        for nwb_path in sorted(split_dir.glob("*.nwb")):
            # session id = the 'ses-...' token in the filename
            ses_token = next(
                (part for part in nwb_path.stem.split("_") if part.startswith("ses-")),
                nwb_path.stem,
            )
            sessions.append(
                Session(
                    path=nwb_path,
                    dataset=dataset,
                    split=split,
                    session_id=ses_token,
                    date=_parse_date(ses_token),
                )
            )
    return sessions


def load_session_arrays(session: Session, cache_dir: Path | None = None):
    """Return (neural, covariate, trial_change, eval_mask) for one session, cached to .npz."""
    cache_path = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{session.dataset}_{session.stem}.npz"
        if cache_path.exists():
            z = np.load(cache_path)
            return z["neural"], z["covariate"], z["trial_change"], z["eval_mask"]

    task = TASK_BY_DATASET[session.dataset]
    neural, covariate, trial_change, eval_mask = load_nwb(session.path, dataset=task)

    if cache_path is not None:
        np.savez_compressed(
            cache_path,
            neural=neural,
            covariate=covariate,
            trial_change=trial_change,
            eval_mask=eval_mask,
        )
    return neural, covariate, trial_change, eval_mask


REPO_ROOT = Path(__file__).resolve().parent.parent


def build_manifest(sessions: list[Session], cache_dir: Path | None = None) -> pd.DataFrame:
    """One row per session: split, date, n_bins, n_units, labeled (eval-mask) minutes."""
    rows = []
    for s in sessions:
        neural, covariate, trial_change, eval_mask = load_session_arrays(s, cache_dir=cache_dir)
        rows.append(
            {
                "dataset": s.dataset,
                "session_id": s.session_id,
                "split": s.split,
                "date": s.date.strftime("%Y-%m-%d"),
                "n_bins": neural.shape[0],
                "n_units": neural.shape[1],
                "n_covariate_dims": covariate.shape[1],
                "eval_bins": int(eval_mask.sum()),
                "labeled_minutes": round(int(eval_mask.sum()) * BIN_SIZE_S / 60, 2),
                "path": str(s.path.resolve().relative_to(REPO_ROOT)),
            }
        )
    df = pd.DataFrame(rows).sort_values(["dataset", "date", "session_id"]).reset_index(drop=True)
    return df
