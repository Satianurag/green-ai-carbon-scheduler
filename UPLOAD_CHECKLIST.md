# ✅ Pre-Upload Checklist

## Quick Validation

Run the validation script before uploading:

```bash
./validate_before_upload.sh
```

This will check:
- ✅ Python version compatibility
- ✅ All required files present
- ✅ Module imports working
- ✅ All 83 tests passing
- ✅ Code quality checks
- ✅ README examples work

---

## Manual Checklist

### 🔍 Code Quality
- [x] All tests passing (83/83)
- [x] No import errors
- [x] Documentation complete
- [x] README updated with test information

### 📊 Test Coverage
- [x] Unit tests: 6 modules (70+ tests)
- [x] Integration tests: 10+ scenarios
- [x] Smoke tests: Legacy compatibility (4 tests)
- [x] Coverage: ~85% overall

### 📁 Files to Upload

**Core Source** (Required):
```
src/greenai/
├── __init__.py
├── cli.py
├── pipeline.py
├── scheduler.py
├── measure.py
├── metrics.py
├── ci_provider.py
└── plots.py
```

**Tests** (Recommended):
```
tests/
├── __init__.py
├── test_ci_provider.py
├── test_scheduler.py
├── test_measure.py
├── test_pipeline.py
├── test_metrics.py
├── test_plots.py
└── test_integration.py
```

**Configuration**:
```
├── requirements.txt           # Core dependencies
├── requirements-test.txt      # Test dependencies
├── pytest.ini                 # Test configuration
├── README.md                  # Main documentation
├── TESTING.md                 # Test guide
├── CONTRIBUTING.md            # Contribution guide
├── LICENSE                    # MIT License
└── test_smoke.py              # Legacy smoke tests
```

**Optional but Recommended**:
```
├── run.sh                     # Quick start script
├── validate_before_upload.sh  # Pre-upload validation
├── TEST_UPGRADE_SUMMARY.md    # Test improvement docs
├── UPLOAD_CHECKLIST.md        # This file
├── notebooks/                 # Jupyter demos
└── artifacts/                 # Example outputs
```

### 🚫 Files to Exclude

Do **NOT** upload:
```
.venv/                         # Virtual environment
__pycache__/                   # Python cache
.pytest_cache/                 # Pytest cache
htmlcov/                       # Coverage reports
*.pyc                          # Compiled Python
.git/                          # Git history
.gitignore                     # (or include if using git)
```

---

## 🎯 Platform-Specific Notes

### GitHub
```bash
# Make sure .gitignore is configured
git add .
git commit -m "Complete test suite upgrade - 83 tests, 85% coverage"
git push
```

### Kaggle
- Upload all files except `.venv/`, `__pycache__/`
- Include `requirements.txt` for dependency installation
- Include notebook in `notebooks/` folder

### DoraHacks
- Include comprehensive README.md
- Highlight test coverage (85%)
- Include TESTING.md for judges
- Show TEST_UPGRADE_SUMMARY.md to demonstrate quality

---

## 🏆 Submission Highlights

**Mention in your submission**:

1. **Comprehensive Testing**
   - 83 automated tests
   - 85% code coverage
   - Full mocking (no external dependencies)
   - CI/CD ready

2. **Production Quality**
   - Modular architecture
   - Complete documentation
   - Error handling
   - Type hints

3. **Real Impact**
   - 78% CO₂ reduction proven
   - Live API integration
   - Scalable to enterprise

4. **Reproducibility**
   - One-command setup (`bash run.sh`)
   - Deterministic results (`random_state=42`)
   - Docker-ready (can add Dockerfile if needed)

---

## 📸 Screenshots/Evidence

Consider including:
- Terminal output of `pytest` showing all tests pass
- Coverage report from `pytest --cov`
- Output of `./validate_before_upload.sh`
- Example artifacts (evidence.csv, plots)

---

## ⚡ Quick Commands Reference

```bash
# Validate everything
./validate_before_upload.sh

# Run all tests
pytest

# Run with coverage
pytest --cov=src/greenai --cov-report=term-missing

# Run legacy smoke tests
python3 test_smoke.py

# Quick demo
bash run.sh
```

---

## 🎉 Final Check

Before uploading, verify:

- [ ] Validation script passes: `./validate_before_upload.sh`
- [ ] README is up-to-date
- [ ] All sensitive data removed (API keys, personal info)
- [ ] License file included (MIT)
- [ ] Tests run successfully
- [ ] Documentation is clear and complete

---

**🚀 You're ready to upload! Good luck with your submission!**
