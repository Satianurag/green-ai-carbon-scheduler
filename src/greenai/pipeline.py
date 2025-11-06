from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any

from sklearn.datasets import fetch_california_housing, make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_selection import SelectFromModel

try:
    # LightGBM provides fast, energy-efficient tree boosting
    from lightgbm import LGBMRegressor
    import lightgbm as lgb
except Exception:  # pragma: no cover - optional dependency
    LGBMRegressor = None  # type: ignore
    lgb = None  # type: ignore


def load_dataset(csv_path: Optional[str] = None, target_col: str = "GreenScore", n_samples: int = 1200, random_state: int = 42) -> Tuple[pd.DataFrame, pd.Series]:
    if csv_path:
        df = pd.read_csv(csv_path)
        if target_col in df.columns:
            y = df[target_col]
            X = df.drop(columns=[target_col])
        else:
            # Fallback: synthetic target from numeric columns
            num = df.select_dtypes(include=[np.number])
            y = num.sum(axis=1)
            X = df.drop(columns=[])
        return X, y
    # Try California Housing; if unavailable (no internet), fallback to synthetic
    try:
        data = fetch_california_housing(as_frame=True)
        df = data.frame.sample(n=min(n_samples, len(data.frame)), random_state=random_state)
        X = df.drop(columns=["MedHouseVal"])
        y = df["MedHouseVal"]
        return X, y
    except Exception:
        X, y = make_regression(n_samples=n_samples, n_features=12, noise=5.0, random_state=random_state)
        X = pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])
        y = pd.Series(y, name="target")
        return X, y


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    transformers = []
    if num_cols:
        transformers.append(("num", StandardScaler(), num_cols))
    if cat_cols:
        # Dense output keeps downstream models simple and LightGBM-compatible
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols))
    return ColumnTransformer(transformers)


def build_baseline_model(random_state: int = 42):
    return GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=random_state,
    )


def build_optimized_model(random_state: int = 42):
    """Fast, energy-efficient GBRT: fewer trees, aggressive subsampling."""
    return GradientBoostingRegressor(
        n_estimators=50,
        learning_rate=0.15,
        max_depth=2,
        subsample=0.6,
        random_state=random_state,
    )


def build_lgbm_model(random_state: int = 42, n_jobs: int = -1) -> Any:
    """Return a tuned LightGBM regressor if available, else fallback to GBRT."""
    if LGBMRegressor is None:
        return build_optimized_model(random_state)
    return LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_data_in_leaf=10,
        reg_alpha=0.0,
        reg_lambda=0.0,
        random_state=random_state,
        n_jobs=n_jobs,
    )


def train_and_eval(
    mode: str,
    csv_path: Optional[str] = None,
    target_col: str = "GreenScore",
    test_size: float = 0.2,
    random_state: int = 42,
    n_jobs: int = -1,
    feature_select: bool = False,
) -> Dict[str, Any]:
    assert mode in {"baseline", "optimized"}
    X, y = load_dataset(csv_path=csv_path, target_col=target_col, random_state=random_state)
    pre = build_preprocessor(X)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=random_state)

    # Small-data heuristics
    use_lgbm_possible = (LGBMRegressor is not None and mode == "optimized")
    if mode == "baseline" or not use_lgbm_possible:
        model = build_baseline_model(random_state) if mode == "baseline" else build_optimized_model(random_state)
        pipe = Pipeline([("prep", pre), ("model", model)])
        pipe.fit(Xtr, ytr)
        preds = pipe.predict(Xte)
        mae = mean_absolute_error(yte, preds)
        return {"mae": float(mae), "pipeline": pipe}

    # Optimized path with LightGBM + early stopping + optional feature selection
    # Fit preprocessor and transform to dense arrays
    pre.fit(Xtr)
    Xtr_enc = pre.transform(Xtr)
    Xte_enc = pre.transform(Xte)
    # Guard: LightGBM overhead only pays off on large datasets (5K+ samples)
    if getattr(Xtr_enc, "shape", (0, 0))[0] < 5000 or getattr(Xtr_enc, "shape", (0, 0))[1] < 5:
        model = build_optimized_model(random_state)
        pipe = Pipeline([("prep", pre), ("model", model)])
        pipe.fit(Xtr, ytr)
        preds = pipe.predict(Xte)
        mae = mean_absolute_error(yte, preds)
        return {"mae": float(mae), "pipeline": pipe}

    model = build_lgbm_model(random_state=random_state, n_jobs=n_jobs)

    if feature_select:
        selector = SelectFromModel(estimator=build_lgbm_model(random_state=random_state, n_jobs=n_jobs), threshold="median")
        selector.fit(Xtr_enc, ytr)
        Xtr_sel = selector.transform(Xtr_enc)
        # Ensure at least 1 feature keeps; else disable selection
        if getattr(Xtr_sel, "shape", (0, 0))[1] >= 1:
            Xtr_enc = Xtr_sel
            Xte_enc = selector.transform(Xte_enc)
        else:
            selector = None
    else:
        selector = None

    # Early stopping using a validation split from training data
    X_tr, X_val, y_tr, y_val = train_test_split(Xtr_enc, ytr, test_size=0.2, random_state=random_state)
    callbacks = []
    if lgb is not None:
        try:
            callbacks.append(lgb.early_stopping(50, verbose=False))
            callbacks.append(lgb.log_evaluation(0))
        except Exception:
            pass
    model.fit(
        X_tr,
        y_tr,
        eval_set=[(X_val, y_val)],
        callbacks=callbacks or None,
    )
    preds = model.predict(Xte_enc)
    mae = mean_absolute_error(yte, preds)
    # Return a callable predictor via a tiny wrapper
    def _predict_fn(Xnew: pd.DataFrame) -> np.ndarray:
        Xnew_enc = pre.transform(Xnew)
        if selector is not None:
            Xnew_enc = selector.transform(Xnew_enc)
        return model.predict(Xnew_enc)

    return {"mae": float(mae), "pipeline": (pre, selector, model, _predict_fn)}


def fit_and_predict(
    *,
    mode: str,
    train_csv: str,
    test_csv: str,
    target_col: str = "GreenScore",
    random_state: int = 42,
    n_jobs: int = -1,
    feature_select: bool = False,
):
    """
    Train on train_csv and predict on test_csv, returning a DataFrame with columns
    Id,GreenScore suitable for Kaggle submission. Automatically detects id/target columns.
    """
    assert mode in {"baseline", "optimized"}
    # Load training data
    df_tr = pd.read_csv(train_csv)
    # Detect target column
    possible_targets = [target_col, "GreenScore", "target"]
    tcol = next((c for c in possible_targets if c in df_tr.columns), None)
    if tcol is None:
        # Fallback: synthesize a target from numeric features
        num = df_tr.select_dtypes(include=[np.number])
        y = num.sum(axis=1)
        X_full = df_tr.drop(columns=[c for c in ["example_id", "Id"] if c in df_tr.columns])
    else:
        y = df_tr[tcol]
        drop_cols = [tcol]
        if "example_id" in df_tr.columns:
            drop_cols.append("example_id")
        if "Id" in df_tr.columns:
            drop_cols.append("Id")
        X_full = df_tr.drop(columns=drop_cols)

    # Load test data
    df_te = pd.read_csv(test_csv)
    id_col = "example_id" if "example_id" in df_te.columns else ("Id" if "Id" in df_te.columns else None)
    Xte_full = df_te.drop(columns=[id_col] if id_col else [])

    # Align on common feature columns between train and test
    common_cols = [c for c in X_full.columns if c in Xte_full.columns]
    if len(common_cols) == 0:
        # No overlapping features; fallback to constant prediction (mean of y)
        const_val = float(getattr(y, "mean", lambda: 0.0)()) if hasattr(y, "mean") else 0.0
        if id_col:
            return pd.DataFrame({"Id": df_te[id_col], "GreenScore": const_val})
        return pd.DataFrame({"Id": [f"ROW{i:06d}" for i in range(len(df_te))], "GreenScore": const_val})

    X = X_full[common_cols]
    Xte = Xte_full[common_cols]

    # Build and fit model on aligned columns
    pre = build_preprocessor(X)
    if mode == "baseline" or LGBMRegressor is None:
        pipe = Pipeline([("prep", pre), ("model", build_baseline_model(random_state) if mode == "baseline" else build_optimized_model(random_state))])
        pipe.fit(X, y)
        preds = pipe.predict(Xte)
    else:
        pre.fit(X)
        X_enc = pre.transform(X)
        Xte_enc = pre.transform(Xte)
        # Guard: LightGBM overhead only pays off on large datasets
        if getattr(X_enc, "shape", (0, 0))[0] < 5000 or getattr(X_enc, "shape", (0, 0))[1] < 5:
            pipe = Pipeline([( "prep", pre), ("model", build_optimized_model(random_state))])
            pipe.fit(X, y)
            preds = pipe.predict(Xte)
        else:
            model = build_lgbm_model(random_state=random_state, n_jobs=n_jobs)
            selector = None
            if feature_select:
                selector = SelectFromModel(estimator=build_lgbm_model(random_state=random_state, n_jobs=n_jobs), threshold="median")
                selector.fit(X_enc, y)
                X_sel = selector.transform(X_enc)
                if getattr(X_sel, "shape", (0, 0))[1] >= 1:
                    X_enc = X_sel
                    Xte_enc = selector.transform(Xte_enc)
                else:
                    selector = None
            # Early stopping: hold out a small validation set from training data
            X_tr, X_val, y_tr, y_val = train_test_split(X_enc, y, test_size=0.1, random_state=random_state)
            callbacks = []
            if lgb is not None:
                try:
                    callbacks.append(lgb.early_stopping(50, verbose=False))
                    callbacks.append(lgb.log_evaluation(0))
                except Exception:
                    pass
            model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], callbacks=callbacks or None)
            preds = model.predict(Xte_enc)
        selector = None
        if feature_select:
            selector = SelectFromModel(estimator=build_lgbm_model(random_state=random_state, n_jobs=n_jobs), threshold="median")
            selector.fit(X_enc, y)
            X_enc = selector.transform(X_enc)
            Xte_enc = selector.transform(Xte_enc)
        # Early stopping: hold out a small validation set from training data
        X_tr, X_val, y_tr, y_val = train_test_split(X_enc, y, test_size=0.1, random_state=random_state)
        callbacks = []
        if lgb is not None:
            try:
                callbacks.append(lgb.early_stopping(50, verbose=False))
                callbacks.append(lgb.log_evaluation(0))
            except Exception:
                pass
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], callbacks=callbacks or None)
        preds = model.predict(Xte_enc)

    # Build submission DataFrame
    if id_col:
        out = pd.DataFrame({"Id": df_te[id_col], "GreenScore": preds})
    else:
        out = pd.DataFrame({"Id": [f"ROW{i:06d}" for i in range(len(preds))], "GreenScore": preds})
    return out
