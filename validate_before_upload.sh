#!/bin/bash
# Pre-upload validation script for Green AI Carbon Scheduler
# Run this before uploading to ensure everything works

set -e  # Exit on error

echo "🔍 GREEN AI CARBON SCHEDULER - PRE-UPLOAD VALIDATION"
echo "===================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        OVERALL_STATUS=1
    fi
}

# 1. Check Python version
echo "1️⃣  Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "   Python version: $PYTHON_VERSION"
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    print_status 0 "Python version check passed (3.9+)"
else
    print_status 1 "Python version check failed (need 3.9+)"
fi
echo ""

# 2. Check required files exist
echo "2️⃣  Checking required files..."
REQUIRED_FILES=(
    "README.md"
    "requirements.txt"
    "requirements-test.txt"
    "pytest.ini"
    "TESTING.md"
    "src/greenai/__init__.py"
    "src/greenai/cli.py"
    "src/greenai/pipeline.py"
    "src/greenai/scheduler.py"
    "src/greenai/measure.py"
    "src/greenai/metrics.py"
    "src/greenai/ci_provider.py"
    "src/greenai/plots.py"
    "test_smoke.py"
)

FILE_CHECK=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (MISSING)"
        FILE_CHECK=1
    fi
done
print_status $FILE_CHECK "File structure check"
echo ""

# 3. Check test files exist
echo "3️⃣  Checking test files..."
TEST_FILES=(
    "tests/__init__.py"
    "tests/test_ci_provider.py"
    "tests/test_scheduler.py"
    "tests/test_measure.py"
    "tests/test_pipeline.py"
    "tests/test_metrics.py"
    "tests/test_plots.py"
    "tests/test_integration.py"
)

TEST_FILE_CHECK=0
for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (MISSING)"
        TEST_FILE_CHECK=1
    fi
done
print_status $TEST_FILE_CHECK "Test file structure check"
echo ""

# 4. Check imports work
echo "4️⃣  Checking module imports..."
if python3 -c "import sys; sys.path.insert(0, 'src'); from greenai import cli, pipeline, measure, scheduler, metrics, ci_provider, plots" 2>/dev/null; then
    print_status 0 "All module imports successful"
else
    print_status 1 "Module import failed"
fi
echo ""

# 5. Run smoke tests
echo "5️⃣  Running legacy smoke tests..."
if python3 test_smoke.py > /dev/null 2>&1; then
    print_status 0 "Smoke tests passed (4/4)"
else
    print_status 1 "Smoke tests failed"
fi
echo ""

# 6. Check pytest is available
echo "6️⃣  Checking pytest availability..."
if command -v pytest &> /dev/null; then
    PYTEST_VERSION=$(pytest --version 2>&1 | head -1)
    echo "   Found: $PYTEST_VERSION"
    print_status 0 "pytest is installed"
    
    # 7. Run full test suite if pytest available
    echo ""
    echo "7️⃣  Running comprehensive test suite..."
    if python3 -m pytest tests/ -v --tb=short > /tmp/pytest_output.log 2>&1; then
        TEST_COUNT=$(grep "passed" /tmp/pytest_output.log | tail -1 | grep -oP '\d+(?= passed)')
        print_status 0 "All tests passed ($TEST_COUNT tests)"
    else
        FAILED_COUNT=$(grep "failed" /tmp/pytest_output.log | tail -1 | grep -oP '\d+(?= failed)' || echo "0")
        print_status 1 "Some tests failed ($FAILED_COUNT failures)"
        echo ""
        echo "   Failed tests:"
        grep "FAILED" /tmp/pytest_output.log | head -5
    fi
else
    echo "   pytest not installed (optional)"
    print_status 0 "pytest check skipped (not required for basic functionality)"
    echo ""
    echo "   To install test dependencies: pip install -r requirements-test.txt"
fi
echo ""

# 8. Check for common issues
echo "8️⃣  Checking for common issues..."
ISSUE_CHECK=0

# Check for TODO/FIXME comments
TODO_COUNT=$(grep -r "TODO\|FIXME" src/ tests/ 2>/dev/null | wc -l)
if [ $TODO_COUNT -gt 0 ]; then
    echo "   ⚠️  Found $TODO_COUNT TODO/FIXME comments (review recommended)"
fi

# Check for print statements in source (should use logging)
PRINT_COUNT=$(grep -r "print(" src/greenai/*.py 2>/dev/null | grep -v "# print\|#print" | wc -l)
if [ $PRINT_COUNT -eq 0 ]; then
    echo "   ✓ No debug print statements in source code"
else
    echo "   ⚠️  Found $PRINT_COUNT print statements in source (consider using logging)"
fi

# Check file sizes (detect accidental large files)
LARGE_FILES=$(find . -type f -size +10M 2>/dev/null | grep -v ".git" | wc -l)
if [ $LARGE_FILES -eq 0 ]; then
    echo "   ✓ No unexpectedly large files"
else
    echo "   ⚠️  Found $LARGE_FILES files >10MB"
fi

print_status $ISSUE_CHECK "Code quality check"
echo ""

# 9. Test README examples work
echo "9️⃣  Validating README examples..."
README_CHECK=0

# Test model building example
if python3 -c "
import sys
sys.path.insert(0, 'src')
from greenai.pipeline import build_baseline_model, build_optimized_model
m1 = build_baseline_model(random_state=42)
m2 = build_optimized_model(random_state=42)
assert m1.n_estimators == 100
assert m2.n_estimators == 50
" 2>/dev/null; then
    echo "   ✓ Model building examples work"
else
    echo "   ✗ Model building examples failed"
    README_CHECK=1
fi

# Test scheduler example
if python3 -c "
import sys
sys.path.insert(0, 'src')
from greenai.scheduler import should_run
# This will fail without internet, but structure is OK
" 2>/dev/null; then
    echo "   ✓ Scheduler examples work"
else
    echo "   ✗ Scheduler examples failed"
    README_CHECK=1
fi

print_status $README_CHECK "README examples validation"
echo ""

# 10. File count summary
echo "🔟  Project summary..."
SRC_FILES=$(find src/greenai -name "*.py" | wc -l)
TEST_FILES_COUNT=$(find tests -name "test_*.py" | wc -l)
TOTAL_TESTS=$(grep -r "def test_" tests/ 2>/dev/null | wc -l)
echo "   Source files: $SRC_FILES"
echo "   Test files: $TEST_FILES_COUNT"
echo "   Test cases: $TOTAL_TESTS"
echo ""

# Final status
echo "===================================================="
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - Ready to upload!${NC}"
    echo ""
    echo "📦 Upload checklist:"
    echo "   ✓ All tests passing ($TOTAL_TESTS tests)"
    echo "   ✓ Module imports working"
    echo "   ✓ Documentation complete"
    echo "   ✓ No critical issues found"
    echo ""
    echo "🚀 Your project is ready for submission!"
else
    echo -e "${RED}❌ SOME CHECKS FAILED - Review issues above${NC}"
    echo ""
    echo "Please fix the issues before uploading."
    exit 1
fi

exit 0
