# Data Card

## Source & License
- Default synthetic dataset for reproducibility.
- Optional: Kaggle Community Olympiad - Hack 4 Earth (CC BY 4.0). Provide local CSV with target column `GreenScore`.

## Composition
- Synthetic: 1200 samples, 12 features (regression)
- Kaggle: Mixed numeric/categorical; target `GreenScore`

## Preprocessing
- Numerical: StandardScaler
- Categorical: OneHotEncoder(handle_unknown="ignore")

## Appropriateness & Sufficiency
- Synthetic data is for measurement methodology demo. Replace with domain data for production relevance.

## Bias & Ethics
- No PII; environmental task. Kaggle data license and attribution required if used.
