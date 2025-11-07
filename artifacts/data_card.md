# 📋 Data Card

## What We're Measuring

**Purpose:** Demonstrate carbon-aware ML scheduling with measurable energy/CO₂ reduction.

**Task:** Regression (predict continuous values) to show model efficiency tradeoffs.

## Data Sources

### Default: California Housing (via scikit-learn)
- **Size:** 1,200 samples, 8 features
- **License:** BSD (open source)
- **Why:** Public dataset, reproducible, no privacy concerns
- **Limitations:** Small size means fast training (good for demo, hits sensor limits)

### Optional: Kaggle Competition Data
- **Source:** Hack4Earth Green AI Competition
- **License:** CC BY 4.0
- **Format:** `train.csv` with target column
- **Note:** Scaffold dataset (minimal features) to enable submissions

## Preprocessing

**Standard ML pipeline:**
- Numeric features → StandardScaler (zero mean, unit variance)
- Categorical features → OneHotEncoder (binary columns)
- Missing values → Forward fill or drop

**Deterministic:** `random_state=42` ensures identical preprocessing across baseline/optimized runs.

## Fitness for Purpose

### ✅ What This Data IS Good For:
- Proving carbon measurement methodology
- Demonstrating carbon-aware scheduling
- Showing model efficiency tradeoffs
- Reproducible benchmarking

### ⚠️ What This Data IS NOT:
- Representative of production workloads (too small)
- Domain-specific sustainability problem
- Long-running training (seconds vs hours)

**For production:** Replace with your domain data. Architecture scales to larger datasets, GPUs, longer training.

## Ethics & Bias

- ✅ No PII (personally identifiable information)
- ✅ No sensitive attributes (race, gender, etc.)
- ✅ Open license (free to use, modify, distribute)
- ✅ Environmental focus (reduce AI carbon footprint)
- ⚠️ Measurement bias: Ultra-short runtimes hit sensor precision limits (see FOOTPRINT.md)
