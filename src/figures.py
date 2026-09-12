
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.io import discover_sessions, load_session_arrays, build_manifest
from src.decoder import WienerFilter

ROOT = Path(__file__).resolve().parent.parent
DATASET_DANDISET = {"m1": "000941", "m2": "000953", "h1": "000954"}


def run(dataset: str, out_path: Path):
    # `dandi download -o data/<id> <url>` nests one extra `<id>/` level under -o.
    data_dir = ROOT / "data" / DATASET_DANDISET[dataset] / DATASET_DANDISET[dataset]
    cache_dir = ROOT / "cache"
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    sessions = discover_sessions(data_dir, dataset)
    if not sessions:
        raise FileNotFoundError(f"No sessions found under {data_dir}. Download the dandiset first.")

    manifest = build_manifest(sessions, cache_dir=cache_dir)
    manifest_path = results_dir / "sessions_manifest.csv"
    if manifest_path.exists():
        prior = pd.read_csv(manifest_path)
        prior = prior[prior["dataset"] != dataset]
        manifest = pd.concat([prior, manifest], ignore_index=True)
    manifest = manifest.sort_values(["dataset", "date", "session_id"]).reset_index(drop=True)
    manifest.to_csv(manifest_path, index=False)
    print(f"wrote {manifest_path} ({len(manifest)} rows total)")

    held_in = [s for s in sessions if s.split == "held-in-calib"]
    held_out = [s for s in sessions if s.split == "held-out-calib"]
    if not held_in or not held_out:
        raise ValueError(f"Expected held-in-calib and held-out-calib sessions for {dataset}, "
                          f"found {len(held_in)} held-in / {len(held_out)} held-out.")

    # --- pool held-in training data, fit the frozen decoder ---
    neural_list, cov_list, tc_list, mask_list, offsets, ids = [], [], [], [], [0], []
    for s in held_in:
        neural, cov, trial_change, eval_mask = load_session_arrays(s, cache_dir=cache_dir)
        neural_list.append(neural)
        cov_list.append(cov)
        tc_list.append(trial_change)
        mask_list.append(eval_mask)
        offsets.append(offsets[-1] + neural.shape[0])
        ids.append(s.session_id)

    pooled_neural = np.concatenate(neural_list, axis=0)
    pooled_cov = np.concatenate(cov_list, axis=0)
    # trial_change per-session flags get OR'd with pooled-session boundaries, so lag
    # windows never straddle a splice between two concatenated sessions either.
    pooled_trial_change = np.concatenate(tc_list, axis=0).copy()
    for off in offsets[1:-1]:
        pooled_trial_change[off] = True
    pooled_eval_mask = np.concatenate(mask_list, axis=0)

    wf = WienerFilter().fit(pooled_neural, pooled_cov, pooled_trial_change, pooled_eval_mask, ids)
    model_path = cache_dir / f"{dataset}_wiener_model.joblib"
    wf.save(model_path)
    print(f"froze decoder: n_lags={wf.n_lags} alpha={wf.alpha} trained on {ids}")

    # --- evaluate every held-in and held-out session under the frozen decoder ---
    rows = []
    train_start_date = min(s.date for s in held_in)
    for s in held_in + held_out:
        neural, cov, trial_change, eval_mask = load_session_arrays(s, cache_dir=cache_dir)
        r2, n_used = wf.score_session(neural, cov, trial_change, eval_mask)
        rows.append({
            "dataset": dataset,
            "session_id": s.session_id,
            "split": s.split,
            "date": s.date.strftime("%Y-%m-%d"),
            "days_elapsed": (s.date - train_start_date).days,
            "r2": r2,
            "n_eval_bins": n_used,
        })
        print(f"  {s.session_id} ({s.split}): R^2 = {r2:.3f}  [n_eval_bins={n_used}]")

    r2_df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    r2_path = results_dir / f"{dataset}_session_r2.csv"
    r2_df.to_csv(r2_path, index=False)
    print(f"wrote {r2_path}")

    pooled_held_in_r2 = r2_df.loc[r2_df.split == "held-in-calib", "r2"].mean()

    # --- figure ---
    fig, ax = plt.subplots(figsize=(8, 5))
    for split, marker, color, label in [
        ("held-in-calib", "o", "#1B6B5E", "held-in"),
        ("held-out-calib", "^", "#B8471B", "held-out"),
    ]:
        sub = r2_df[r2_df.split == split]
        ax.scatter(sub.days_elapsed, sub.r2, marker=marker, color=color, s=70,
                   label=label, zorder=3, edgecolor="white", linewidth=0.5)
    ax.axhline(pooled_held_in_r2, color="#7E8896", linestyle="--", linewidth=1,
               label=f"pooled held-in R² = {pooled_held_in_r2:.2f}", zorder=1)
    ax.axhline(0, color="#D3D8DE", linewidth=1, zorder=0)
    ax.set_xlabel("Days since training session")
    ax.set_ylabel("R² (variance-weighted)")
    ax.set_title(f"{dataset.upper()} decoder degradation over days elapsed")
    y_lo = min(0, r2_df.r2.min()) - 0.05
    y_hi = max(1, r2_df.r2.max()) if r2_df.r2.max() > 0.9 else 1.0
    ax.set_ylim(y_lo, y_hi)
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    print(f"wrote {out_path}")

    return r2_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="m1", choices=["m1", "m2", "h1"])
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    run(args.dataset, args.out)
