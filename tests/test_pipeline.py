#!/usr/bin/env python3
"""
Unit tests for greenai.pipeline module.
Tests model building, data loading, and ML pipeline functionality.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from greenai.pipeline import (
    load_dataset,
    build_preprocessor,
    build_baseline_model,
    build_optimized_model,
    build_lgbm_model,
    train_and_eval,
    fit_and_predict,
)


class TestLoadDataset:
    """Test dataset loading functionality."""

    def test_load_from_csv_with_target(self, tmp_path):
        """Test loading dataset from CSV with GreenScore column."""
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({
            "feature1": [1, 2, 3, 4],
            "feature2": [5, 6, 7, 8],
            "GreenScore": [10, 20, 30, 40]
        })
        df.to_csv(csv_path, index=False)
        
        X, y = load_dataset(csv_path=str(csv_path))
        
        assert len(X) == 4
        assert "GreenScore" not in X.columns
        assert "feature1" in X.columns
        assert list(y) == [10, 20, 30, 40]

    def test_load_from_csv_without_target(self, tmp_path):
        """Test fallback when target column is missing."""
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({
            "feature1": [1, 2, 3],
            "feature2": [4, 5, 6],
        })
        df.to_csv(csv_path, index=False)
        
        X, y = load_dataset(csv_path=str(csv_path), target_col="GreenScore")
        
        # Should synthesize target from numeric columns
        assert len(X) == 3
        assert len(y) == 3

    @patch('greenai.pipeline.fetch_california_housing')
    def test_load_california_housing(self, mock_fetch):
        """Test loading California Housing dataset."""
        mock_data = Mock()
        mock_data.frame = pd.DataFrame({
            "MedInc": [1.0, 2.0] * 600,
            "HouseAge": [10, 20] * 600,
            "MedHouseVal": [100, 200] * 600
        })
        mock_fetch.return_value = mock_data
        
        X, y = load_dataset(csv_path=None, n_samples=1200)
        
        assert len(X) == 1200
        assert "MedHouseVal" not in X.columns
        assert len(y) == 1200

    @patch('greenai.pipeline.fetch_california_housing')
    def test_load_synthetic_fallback(self, mock_fetch):
        """Test fallback to synthetic data when California Housing unavailable."""
        mock_fetch.side_effect = Exception("No internet")
        
        X, y = load_dataset(csv_path=None, n_samples=500)
        
        assert len(X) == 500
        assert len(y) == 500
        assert X.shape[1] == 12  # 12 features


class TestBuildPreprocessor:
    """Test preprocessing pipeline construction."""

    def test_numeric_only_preprocessor(self):
        """Test preprocessor with only numeric features."""
        X = pd.DataFrame({
            "num1": [1, 2, 3],
            "num2": [4.5, 5.5, 6.5]
        })
        
        preprocessor = build_preprocessor(X)
        
        # Should have only numeric transformer
        assert len(preprocessor.transformers) == 1
        assert preprocessor.transformers[0][0] == "num"

    def test_mixed_preprocessor(self):
        """Test preprocessor with numeric and categorical features."""
        X = pd.DataFrame({
            "num1": [1, 2, 3],
            "cat1": ["A", "B", "A"]
        })
        
        preprocessor = build_preprocessor(X)
        
        # Should have both transformers
        assert len(preprocessor.transformers) == 2
        names = [t[0] for t in preprocessor.transformers]
        assert "num" in names
        assert "cat" in names

    def test_categorical_only_preprocessor(self):
        """Test preprocessor with only categorical features."""
        X = pd.DataFrame({
            "cat1": ["A", "B", "C"],
            "cat2": ["X", "Y", "Z"]
        })
        
        preprocessor = build_preprocessor(X)
        
        # Should have only categorical transformer
        assert len(preprocessor.transformers) == 1
        assert preprocessor.transformers[0][0] == "cat"


class TestBuildModels:
    """Test model building functions."""

    def test_baseline_model_config(self):
        """Test baseline model has correct configuration."""
        model = build_baseline_model(random_state=42)
        
        assert model.n_estimators == 100
        assert model.learning_rate == 0.1
        assert model.max_depth == 3
        assert model.random_state == 42

    def test_optimized_model_config(self):
        """Test optimized model has efficient configuration."""
        model = build_optimized_model(random_state=42)
        
        assert model.n_estimators == 50  # Fewer trees
        assert model.learning_rate == 0.15
        assert model.max_depth == 2  # Shallower
        assert model.subsample == 0.6  # Aggressive subsampling
        assert model.random_state == 42

    def test_baseline_vs_optimized_estimators(self):
        """Test that optimized model has fewer estimators than baseline."""
        baseline = build_baseline_model()
        optimized = build_optimized_model()
        
        assert optimized.n_estimators < baseline.n_estimators
        assert optimized.max_depth <= baseline.max_depth

    def test_lgbm_model_fallback(self):
        """Test LightGBM model fallback when unavailable."""
        with patch('greenai.pipeline.LGBMRegressor', None):
            model = build_lgbm_model(random_state=42)
            
            # Should fallback to optimized GBRT
            assert hasattr(model, 'n_estimators')


class TestTrainAndEval:
    """Test complete training and evaluation pipeline."""

    def test_baseline_mode(self):
        """Test training in baseline mode."""
        result = train_and_eval(
            mode="baseline",
            csv_path=None,
            random_state=42,
            n_jobs=1
        )
        
        assert "mae" in result
        assert "pipeline" in result
        assert result["mae"] > 0

    def test_optimized_mode(self):
        """Test training in optimized mode."""
        result = train_and_eval(
            mode="optimized",
            csv_path=None,
            random_state=42,
            n_jobs=1
        )
        
        assert "mae" in result
        assert "pipeline" in result
        assert result["mae"] > 0

    def test_consistent_results_with_seed(self):
        """Test that same seed produces consistent results."""
        result1 = train_and_eval(mode="baseline", random_state=42, n_jobs=1)
        result2 = train_and_eval(mode="baseline", random_state=42, n_jobs=1)
        
        # MAE should be identical with same seed
        assert abs(result1["mae"] - result2["mae"]) < 1e-6

    def test_custom_csv_data(self, tmp_path):
        """Test training with custom CSV data."""
        csv_path = tmp_path / "train.csv"
        df = pd.DataFrame({
            "feature1": np.random.rand(100),
            "feature2": np.random.rand(100),
            "GreenScore": np.random.rand(100) * 10
        })
        df.to_csv(csv_path, index=False)
        
        result = train_and_eval(
            mode="baseline",
            csv_path=str(csv_path),
            random_state=42,
            n_jobs=1
        )
        
        assert result["mae"] > 0
        assert result["mae"] < 100  # Reasonable range

    def test_invalid_mode(self):
        """Test error handling for invalid mode."""
        with pytest.raises(AssertionError):
            train_and_eval(mode="invalid", random_state=42)

    def test_feature_selection_flag(self):
        """Test that feature selection can be enabled."""
        # Only works with larger datasets and LightGBM
        result = train_and_eval(
            mode="optimized",
            csv_path=None,
            random_state=42,
            feature_select=True,
            n_jobs=1
        )
        
        assert "mae" in result


class TestFitAndPredict:
    """Test prediction on new data."""

    def test_predict_with_id_column(self, tmp_path):
        """Test prediction with proper ID column."""
        train_csv = tmp_path / "train.csv"
        test_csv = tmp_path / "test.csv"
        
        train_df = pd.DataFrame({
            "Id": [1, 2, 3, 4, 5],
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature2": [2.0, 3.0, 4.0, 5.0, 6.0],
            "GreenScore": [10, 20, 30, 40, 50]
        })
        test_df = pd.DataFrame({
            "Id": [6, 7, 8],
            "feature1": [6.0, 7.0, 8.0],
            "feature2": [7.0, 8.0, 9.0]
        })
        
        train_df.to_csv(train_csv, index=False)
        test_df.to_csv(test_csv, index=False)
        
        result = fit_and_predict(
            mode="baseline",
            train_csv=str(train_csv),
            test_csv=str(test_csv),
            random_state=42,
            n_jobs=1
        )
        
        assert len(result) == 3
        assert "Id" in result.columns
        assert "GreenScore" in result.columns
        assert list(result["Id"]) == [6, 7, 8]

    def test_predict_without_id_column(self, tmp_path):
        """Test prediction when ID column is missing."""
        train_csv = tmp_path / "train.csv"
        test_csv = tmp_path / "test.csv"
        
        train_df = pd.DataFrame({
            "feature1": [1.0, 2.0, 3.0],
            "GreenScore": [10, 20, 30]
        })
        test_df = pd.DataFrame({
            "feature1": [4.0, 5.0]
        })
        
        train_df.to_csv(train_csv, index=False)
        test_df.to_csv(test_csv, index=False)
        
        result = fit_and_predict(
            mode="baseline",
            train_csv=str(train_csv),
            test_csv=str(test_csv),
            random_state=42,
            n_jobs=1
        )
        
        assert len(result) == 2
        assert "Id" in result.columns
        assert "GreenScore" in result.columns

    def test_predict_optimized_mode(self, tmp_path):
        """Test prediction in optimized mode."""
        train_csv = tmp_path / "train.csv"
        test_csv = tmp_path / "test.csv"
        
        train_df = pd.DataFrame({
            "feature1": np.random.rand(50),
            "feature2": np.random.rand(50),
            "GreenScore": np.random.rand(50) * 100
        })
        test_df = pd.DataFrame({
            "feature1": np.random.rand(10),
            "feature2": np.random.rand(10)
        })
        
        train_df.to_csv(train_csv, index=False)
        test_df.to_csv(test_csv, index=False)
        
        result = fit_and_predict(
            mode="optimized",
            train_csv=str(train_csv),
            test_csv=str(test_csv),
            random_state=42,
            n_jobs=1
        )
        
        assert len(result) == 10
        assert all(result["GreenScore"].notna())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
