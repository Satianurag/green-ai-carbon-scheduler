#!/usr/bin/env python3
"""
Unit tests for greenai.scheduler module.
Tests threshold-based decision logic and decision structure.
"""
import pytest
import sys
from unittest.mock import patch, Mock
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from greenai.scheduler import should_run


class TestShouldRun:
    """Test carbon-aware scheduling logic."""

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_should_run_below_threshold(self, mock_fetch):
        """Test that jobs run when CI is below threshold."""
        mock_fetch.return_value = 150
        
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        
        assert can_run is True
        assert decision["carbon_intensity"] == 150
        assert decision["threshold"] == 200
        assert decision["region"] == "GB"

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_should_not_run_above_threshold(self, mock_fetch):
        """Test that jobs defer when CI is above threshold."""
        mock_fetch.return_value = 250
        
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        
        assert can_run is False
        assert decision["carbon_intensity"] == 250
        assert decision["threshold"] == 200

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_should_run_at_threshold(self, mock_fetch):
        """Test boundary condition when CI equals threshold."""
        mock_fetch.return_value = 200
        
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        
        # At threshold, should not run (strictly less than)
        assert can_run is False
        assert decision["carbon_intensity"] == 200

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_decision_structure(self, mock_fetch):
        """Test that decision dict contains all required fields."""
        mock_fetch.return_value = 150
        
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        
        required_fields = ["timestamp_utc", "region", "carbon_intensity", "threshold"]
        for field in required_fields:
            assert field in decision

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_timestamp_format(self, mock_fetch):
        """Test that timestamp is valid ISO format."""
        mock_fetch.return_value = 150
        
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        
        # Should parse as valid ISO timestamp
        timestamp = datetime.fromisoformat(decision["timestamp_utc"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_custom_threshold(self, mock_fetch):
        """Test custom threshold values."""
        mock_fetch.return_value = 100
        
        can_run, decision = should_run(threshold_gco2_per_kwh=50)
        
        assert can_run is False
        assert decision["threshold"] == 50

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_zero_threshold(self, mock_fetch):
        """Test edge case with zero threshold."""
        mock_fetch.return_value = 0
        
        can_run, decision = should_run(threshold_gco2_per_kwh=0)
        
        # 0 is not less than 0
        assert can_run is False

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_api_failure_propagates(self, mock_fetch):
        """Test that API failures are propagated."""
        mock_fetch.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            should_run(threshold_gco2_per_kwh=200)

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_high_ci_value(self, mock_fetch):
        """Test with very high CI values."""
        mock_fetch.return_value = 500
        
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        
        assert can_run is False
        assert decision["carbon_intensity"] == 500

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_low_ci_value(self, mock_fetch):
        """Test with very low CI values."""
        mock_fetch.return_value = 10
        
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        
        assert can_run is True
        assert decision["carbon_intensity"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
