# 🧪 Testing Guide for Green AI Carbon Scheduler

## Overview

This project now includes a comprehensive test suite covering:
- **Unit tests**: Individual module functionality
- **Integration tests**: End-to-end workflows
- **Mocked tests**: No external dependencies (API, internet)
- **Edge case coverage**: Error handling, boundary conditions

## 📊 Test Coverage

### Current Coverage by Module

| Module | Unit Tests | Coverage | Test File |
|--------|-----------|----------|-----------|
| **ci_provider.py** | 20+ tests | ~90% | `tests/test_ci_provider.py` |
| **scheduler.py** | 11 tests | ~95% | `tests/test_scheduler.py` |
| **measure.py** | 14 tests | ~90% | `tests/test_measure.py` |
| **pipeline.py** | 18+ tests | ~85% | `tests/test_pipeline.py` |
| **metrics.py** | 11 tests | ~80% | `tests/test_metrics.py` |
| **plots.py** | 7 tests | ~85% | `tests/test_plots.py` |
| **Integration** | 10+ tests | N/A | `tests/test_integration.py` |

**Total: 90+ test cases** covering critical functionality.

---

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `requests-mock` - HTTP mocking

### 2. Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_ci_provider.py

# Run specific test class
pytest tests/test_scheduler.py::TestShouldRun

# Run specific test
pytest tests/test_measure.py::TestEnergyCO2Proxy::test_basic_calculation
```

### 3. View Coverage Report

```bash
# Terminal report (generated automatically)
pytest --cov=src/greenai --cov-report=term-missing

# HTML report (open in browser)
pytest --cov=src/greenai --cov-report=html
open htmlcov/index.html
```

---

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_ci_provider.py         # Carbon intensity provider tests
├── test_scheduler.py           # Scheduling logic tests
├── test_measure.py             # Energy measurement tests
├── test_pipeline.py            # ML pipeline tests
├── test_metrics.py             # Metrics collection tests
├── test_plots.py               # Visualization tests
└── test_integration.py         # End-to-end workflow tests
```

---

## 🔬 Test Categories

### Unit Tests

**Purpose**: Test individual functions and classes in isolation.

**Examples**:
```bash
# Test carbon intensity fetching
pytest tests/test_ci_provider.py::TestFetchUKCurrentCI -v

# Test energy calculations
pytest tests/test_measure.py::TestEnergyCO2Proxy -v

# Test model building
pytest tests/test_pipeline.py::TestBuildModels -v
```

### Integration Tests

**Purpose**: Test complete workflows and module interactions.

**Examples**:
```bash
# Test complete training workflow
pytest tests/test_integration.py::TestEndToEndWorkflow -v

# Test Kaggle submission workflow
pytest tests/test_integration.py::test_kaggle_submission_workflow -v
```

### Smoke Tests (Legacy)

**Purpose**: Quick sanity checks for basic functionality.

```bash
# Original smoke tests (still functional)
python test_smoke.py
```

---

## 🛡️ What's Tested

### 1. Carbon Intensity Provider (`test_ci_provider.py`)

✅ Live API integration (mocked)  
✅ Forecast fallback when actual is None  
✅ HTTP error handling  
✅ Timeout handling  
✅ CSV parsing  
✅ Low-CI window selection  
✅ Horizon-based selection  
✅ Region filtering  
✅ Edge cases (empty data, missing columns)

### 2. Scheduler (`test_scheduler.py`)

✅ Threshold-based decisions  
✅ Below/above/at threshold scenarios  
✅ Decision structure validation  
✅ Timestamp format verification  
✅ API failure propagation  
✅ Custom threshold values  
✅ Edge cases (zero threshold, high/low CI)

### 3. Measurement (`test_measure.py`)

✅ Energy/CO2 proxy calculations  
✅ Runtime measurement accuracy  
✅ CodeCarbon integration (mocked)  
✅ Proxy fallback when CodeCarbon unavailable  
✅ Function kwargs support  
✅ Exception propagation  
✅ Edge cases (zero runtime, custom power)

### 4. Pipeline (`test_pipeline.py`)

✅ CSV data loading  
✅ California Housing dataset  
✅ Synthetic data fallback  
✅ Preprocessing (numeric/categorical)  
✅ Baseline vs optimized models  
✅ LightGBM integration  
✅ Feature selection  
✅ Training reproducibility  
✅ Prediction workflows  
✅ Kaggle submission format

### 5. Metrics (`test_metrics.py`)

✅ Evidence CSV creation  
✅ CSV structure validation  
✅ Decision logging to JSON  
✅ Multiple runs append correctly  
✅ Custom dataset support  
✅ Threshold enforcement  
✅ Notes field handling  
✅ Invalid mode error handling

### 6. Plots (`test_plots.py`)

✅ Plot file creation  
✅ Output directory creation  
✅ Multiple runs aggregation  
✅ Missing file error handling  
✅ Malformed data handling  
✅ Path validation

### 7. Integration (`test_integration.py`)

✅ Baseline → Optimized → Plotting workflow  
✅ Scheduler decision making  
✅ Kaggle submission workflow  
✅ CSV-based CI workflow  
✅ Decision logging across runs  
✅ API failure handling  
✅ Data consistency  
✅ Random seed reproducibility

---

## 🎯 Running Specific Test Scenarios

### Fast Tests (No External Dependencies)

```bash
# All tests are mocked - no internet required
pytest tests/
```

### Coverage Goals

```bash
# Generate coverage report
pytest --cov=src/greenai --cov-report=term-missing

# Fail if coverage below 80%
pytest --cov=src/greenai --cov-fail-under=80
```

### Parallel Execution (Faster)

```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

---

## 🐛 Debugging Failed Tests

### Verbose Output

```bash
pytest -vv -s tests/test_ci_provider.py
```

### Show Print Statements

```bash
pytest -s tests/
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Detailed Traceback

```bash
pytest --tb=long
```

---

## ✅ CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=src/greenai --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## 📈 Continuous Improvement

### Adding New Tests

1. **Identify untested code**: Check coverage report
2. **Create test file**: Follow naming convention `test_*.py`
3. **Write test cases**: Use descriptive names
4. **Run tests**: Verify they pass
5. **Check coverage**: Ensure coverage increases

### Test Naming Convention

```python
# Good test names
def test_fetch_actual_ci():
    """Test successful fetch with actual intensity value."""
    
def test_api_timeout():
    """Test handling of timeout errors."""

# Bad test names
def test_1():
    """Test something."""
```

---

## 🔧 Troubleshooting

### ModuleNotFoundError

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest
```

### Import Errors

```bash
# Install in development mode
pip install -e .
```

### Coverage Not Working

```bash
# Reinstall coverage tools
pip install --upgrade pytest-cov coverage
```

---

## 📚 Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---


**Made with 💚 for reliable, carbon-aware AI**
