#!/usr/bin/env python3
"""
Unit tests for greenai.ci_provider module.
Tests API interaction, CSV parsing, and horizon-based selection.
"""
import pytest
import pandas as pd
import sys
from unittest.mock import patch, Mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from greenai.ci_provider import (
    fetch_uk_current_ci,
    read_meta_csv,
    pick_low_ci_window,
    pick_low_ci_within_horizon,
)


class TestFetchUKCurrentCI:
    """Test live API integration and error handling."""

    @patch('greenai.ci_provider.requests.get')
    def test_fetch_actual_ci(self, mock_get):
        """Test successful fetch with actual intensity value."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"intensity": {"actual": 150, "forecast": 200}}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_uk_current_ci()
        assert result == 150
        mock_get.assert_called_once()

    @patch('greenai.ci_provider.requests.get')
    def test_fetch_forecast_fallback(self, mock_get):
        """Test fallback to forecast when actual is None."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"intensity": {"actual": None, "forecast": 180}}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_uk_current_ci()
        assert result == 180

    @patch('greenai.ci_provider.requests.get')
    def test_fetch_with_timeout(self, mock_get):
        """Test custom timeout parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"intensity": {"actual": 100, "forecast": 100}}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetch_uk_current_ci(timeout=15)
        mock_get.assert_called_with(
            "https://api.carbonintensity.org.uk/intensity",
            timeout=15
        )

    @patch('greenai.ci_provider.requests.get')
    def test_api_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_get.return_value.raise_for_status.side_effect = Exception("404 Not Found")
        
        with pytest.raises(Exception):
            fetch_uk_current_ci()

    @patch('greenai.ci_provider.requests.get')
    def test_api_timeout(self, mock_get):
        """Test handling of timeout errors."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout
        
        with pytest.raises(requests.exceptions.Timeout):
            fetch_uk_current_ci()

    @patch('greenai.ci_provider.requests.get')
    def test_api_malformed_response(self, mock_get):
        """Test handling of malformed JSON response."""
        mock_response = Mock()
        mock_response.json.return_value = {"unexpected": "format"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(KeyError):
            fetch_uk_current_ci()


class TestReadMetaCSV:
    """Test CSV reading functionality."""

    def test_read_valid_csv(self, tmp_path):
        """Test reading a valid CSV file."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(
            "region,UTC_hour,carbon_intensity_gco2_per_kwh\n"
            "GB,0,150\n"
            "GB,1,120\n"
        )
        
        df = read_meta_csv(str(csv_path))
        assert len(df) == 2
        assert "carbon_intensity_gco2_per_kwh" in df.columns
        assert df["carbon_intensity_gco2_per_kwh"].iloc[0] == 150

    def test_read_missing_file(self):
        """Test error handling for missing CSV file."""
        with pytest.raises(FileNotFoundError):
            read_meta_csv("/nonexistent/path.csv")


class TestPickLowCIWindow:
    """Test low carbon intensity window selection."""

    def test_pick_minimum_ci(self):
        """Test selection of row with minimum CI."""
        df = pd.DataFrame({
            "region": ["GB", "GB", "GB"],
            "UTC_hour": [0, 1, 2],
            "carbon_intensity_gco2_per_kwh": [200, 100, 150]
        })
        
        result = pick_low_ci_window(df)
        assert result["carbon_intensity_gco2_per_kwh"] == 100.0
        assert result["utc_hour"] == 1

    def test_pick_with_region_filter(self):
        """Test filtering by specific region."""
        df = pd.DataFrame({
            "region": ["GB", "FR", "GB"],
            "UTC_hour": [0, 1, 2],
            "carbon_intensity_gco2_per_kwh": [200, 50, 150]
        })
        
        result = pick_low_ci_window(df, region="GB")
        assert result["carbon_intensity_gco2_per_kwh"] == 150.0
        assert result["region"] == "GB"

    def test_pick_without_region_column(self):
        """Test handling of data without region column."""
        df = pd.DataFrame({
            "UTC_hour": [0, 1, 2],
            "carbon_intensity_gco2_per_kwh": [200, 100, 150]
        })
        
        result = pick_low_ci_window(df, region="GB")
        assert result["carbon_intensity_gco2_per_kwh"] == 100.0
        assert result["region"] == "GB"


class TestPickLowCIWithinHorizon:
    """Test horizon-based carbon intensity selection."""

    @patch('greenai.ci_provider.datetime')
    def test_pick_within_horizon(self, mock_datetime):
        """Test selection within specified time horizon."""
        # Mock current time to 10:00 UTC
        mock_now = Mock()
        mock_now.hour = 10
        mock_datetime.now.return_value = mock_now

        df = pd.DataFrame({
            "region": ["GB"] * 4,
            "UTC_hour": [9, 11, 13, 15],  # hours relative to now: -1, +1, +3, +5
            "carbon_intensity_gco2_per_kwh": [200, 80, 90, 70]
        })
        
        # Horizon of 3 hours: should select from hours 11, 13 (not 15)
        result = pick_low_ci_within_horizon(df, horizon_hours=3)
        assert result["carbon_intensity_gco2_per_kwh"] == 80.0
        assert result["utc_hour"] == 11

    @patch('greenai.ci_provider.datetime')
    def test_pick_with_wraparound(self, mock_datetime):
        """Test horizon calculation with day wraparound."""
        # Mock current time to 23:00 UTC
        mock_now = Mock()
        mock_now.hour = 23
        mock_datetime.now.return_value = mock_now

        df = pd.DataFrame({
            "region": ["GB"] * 3,
            "UTC_hour": [22, 23, 1],  # 1 hour wraps around midnight
            "carbon_intensity_gco2_per_kwh": [200, 150, 100]
        })
        
        result = pick_low_ci_within_horizon(df, horizon_hours=2)
        assert result["carbon_intensity_gco2_per_kwh"] == 100.0

    def test_pick_without_horizon(self):
        """Test global minimum selection when horizon is 0."""
        df = pd.DataFrame({
            "region": ["GB"] * 3,
            "UTC_hour": [0, 12, 23],
            "carbon_intensity_gco2_per_kwh": [200, 50, 150]
        })
        
        result = pick_low_ci_within_horizon(df, horizon_hours=0)
        assert result["carbon_intensity_gco2_per_kwh"] == 50.0

    def test_pick_empty_region(self):
        """Test fallback when region filter yields no results."""
        df = pd.DataFrame({
            "region": ["GB"] * 3,
            "UTC_hour": [0, 1, 2],
            "carbon_intensity_gco2_per_kwh": [200, 100, 150]
        })
        
        result = pick_low_ci_within_horizon(df, horizon_hours=0, region="FR")
        # Should fallback to global minimum
        assert result["carbon_intensity_gco2_per_kwh"] == 100.0

    def test_pick_without_utc_hour(self):
        """Test handling of data without UTC_hour column."""
        df = pd.DataFrame({
            "region": ["GB"] * 3,
            "carbon_intensity_gco2_per_kwh": [200, 100, 150]
        })
        
        result = pick_low_ci_within_horizon(df, horizon_hours=5)
        assert result["carbon_intensity_gco2_per_kwh"] == 100.0
        assert result["utc_hour"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
