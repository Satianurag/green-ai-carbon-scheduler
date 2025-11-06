from __future__ import annotations
import argparse
import os
from typing import Optional

from .metrics import run_once
from .plots import plot_energy_co2_bars
from .pipeline import fit_and_predict


def _positive_int(value: str) -> int:
    iv = int(value)
    if iv < 0:
        raise argparse.ArgumentTypeError("must be >=0")
    return iv


def main():
    p = argparse.ArgumentParser(prog="greenai", description="Carbon-aware ML runner")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="Run one baseline/optimized job and append to evidence.csv")
    pr.add_argument("--mode", choices=["baseline", "optimized"], required=True)
    pr.add_argument("--ci", choices=["live", "csv"], default="live")
    pr.add_argument("--ci-csv", type=str, help="Path to metaData.csv if --ci csv")
    pr.add_argument("--threshold", type=int, default=200)
    pr.add_argument("--defer-seconds", type=_positive_int, default=0)
    pr.add_argument("--assumed-kw", type=float, default=0.1)
    pr.add_argument("--data-csv", type=str, default=None, help="Optional dataset CSV with target 'GreenScore'")
    pr.add_argument("--out", type=str, required=True, help="Path to artifacts/evidence.csv")
    pr.add_argument("--log-decision", type=str, default=None, help="Path to artifacts/carbon_aware_decision.json")
    pr.add_argument("--horizon-hours", type=int, default=0, help="Forecast horizon (hours) for best CI selection when --ci csv")
    pr.add_argument("--max-wait-seconds", type=_positive_int, default=0, help="Max wait for green window (live mode)")
    pr.add_argument("--n-jobs", type=int, default=-1, help="Threads for model training")
    pr.add_argument("--seed", type=int, default=42, help="Random seed")
    pr.add_argument("--feature-select", action="store_true", help="Enable model-based feature selection")
    pr.add_argument("--proxy-emissions", action="store_true", help="Use proxy emissions instead of CodeCarbon")

    pe = sub.add_parser("experiment", help="Run multiple trials and produce plots")
    pe.add_argument("--runs", type=int, default=10)
    pe.add_argument("--ci", choices=["live", "csv"], default="live")
    pe.add_argument("--ci-csv", type=str, help="Path to metaData.csv if --ci csv")
    pe.add_argument("--threshold", type=int, default=200)
    pe.add_argument("--defer-seconds", type=_positive_int, default=0)
    pe.add_argument("--assumed-kw", type=float, default=0.1)
    pe.add_argument("--data-csv", type=str, default=None)
    pe.add_argument("--out", type=str, required=True)
    pe.add_argument("--plots", type=str, default=None)
    pe.add_argument("--horizon-hours", type=int, default=0)
    pe.add_argument("--max-wait-seconds", type=_positive_int, default=0)
    pe.add_argument("--n-jobs", type=int, default=-1)
    pe.add_argument("--seed", type=int, default=42)
    pe.add_argument("--feature-select", action="store_true")
    pe.add_argument("--proxy-emissions", action="store_true")

    pp = sub.add_parser("predict", help="Train on train CSV and predict test CSV into Kaggle submission format")
    pp.add_argument("--mode", choices=["baseline", "optimized"], required=True)
    pp.add_argument("--train-csv", type=str, required=True)
    pp.add_argument("--test-csv", type=str, required=True)
    pp.add_argument("--target-col", type=str, default="GreenScore")
    pp.add_argument("--out", type=str, required=True, help="Path to write submission CSV (Id,GreenScore)")
    pp.add_argument("--n-jobs", type=int, default=-1)
    pp.add_argument("--seed", type=int, default=42)
    pp.add_argument("--feature-select", action="store_true")

    args = p.parse_args()

    if args.cmd == "run":
        row = run_once(
            mode=args.mode,
            dataset_csv=args.data_csv,
            out_path=args.out,
            threshold=args.threshold,
            defer_seconds=args.defer_seconds,
            assumed_kw=args.assumed_kw,
            ci_mode=args.ci,
            ci_csv_path=args.ci_csv,
            log_decision_path=args.log_decision,
            horizon_hours=args.horizon_hours,
            max_wait_seconds=args.max_wait_seconds,
            n_jobs=args.n_jobs,
            random_state=args.seed,
            feature_select=args.feature_select,
            use_codecarbon=(not args.proxy_emissions),
        )
        print("Wrote evidence row:", row)
    elif args.cmd == "experiment":
        for i in range(args.runs):
            mode = "baseline" if i % 2 == 0 else "optimized"
            run_once(
                mode=mode,
                dataset_csv=args.data_csv,
                out_path=args.out,
                threshold=args.threshold,
                defer_seconds=args.defer_seconds,
                assumed_kw=args.assumed_kw,
                ci_mode=args.ci,
                ci_csv_path=args.ci_csv,
                horizon_hours=args.horizon_hours,
                max_wait_seconds=args.max_wait_seconds,
                n_jobs=args.n_jobs,
                random_state=args.seed,
                feature_select=args.feature_select,
                use_codecarbon=(not args.proxy_emissions),
            )
        if args.plots:
            fp = plot_energy_co2_bars(args.out, args.plots)
            print("Saved plot:", fp)
    else:  # predict
        df_sub = fit_and_predict(
            mode=args.mode,
            train_csv=args.train_csv,
            test_csv=args.test_csv,
            target_col=args.target_col,
            n_jobs=args.n_jobs,
            feature_select=args.feature_select,
            random_state=args.seed,
        )
        df_sub.to_csv(args.out, index=False)
        print("Wrote submission:", args.out, "rows:", len(df_sub))


if __name__ == "__main__":
    main()
