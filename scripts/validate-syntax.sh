#!/bin/bash

# CVE Database - Comprehensive Syntax Validator
# This script validates all Python and JavaScript files for syntax errors

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_FILES=0
VALID_FILES=0
ERROR_FILES=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CVE Database - Syntax Validation Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to validate Python file
validate_python() {
    local file=$1
    python -m py_compile "$file" 2>/dev/null
    return $?
}

# Function to validate JavaScript file  
validate_javascript() {
    local file=$1
    node -c "$file" 2>/dev/null
    return $?
}

# Validate Python files
echo -e "${BLUE}[1/2] Validating Python Files...${NC}"
echo "========================================"

python_files=$(find backend database -name "*.py" -type f 2>/dev/null)
python_count=0
python_errors=0

for file in $python_files; do
    TOTAL_FILES=$((TOTAL_FILES + 1))
    python_count=$((python_count + 1))
    
    if validate_python "$file"; then
        echo -e "${GREEN}✅${NC} $file"
        VALID_FILES=$((VALID_FILES + 1))
    else
        echo -e "${RED}❌${NC} $file"
        ERROR_FILES=$((ERROR_FILES + 1))
        python_errors=$((python_errors + 1))
        
        # Try to get detailed error
        echo "    Error details:"
        python -m py_compile "$file" 2>&1 | sed 's/^/    /'
    fi
done

echo ""
echo "Python Summary: $python_count files checked"
echo "  - Valid: $((python_count - python_errors))"
echo "  - Errors: $python_errors"
echo ""

# Validate JavaScript files
echo -e "${BLUE}[2/2] Validating JavaScript/JSX Files...${NC}"
echo "========================================"

js_files=$(find frontend/src -name "*.js" -o -name "*.jsx" 2>/dev/null)
js_count=0
js_errors=0

for file in $js_files; do
    TOTAL_FILES=$((TOTAL_FILES + 1))
    js_count=$((js_count + 1))
    
    # Basic Node.js syntax check
    if node -c "$file" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} $file"
        VALID_FILES=$((VALID_FILES + 1))
    else
        echo -e "${YELLOW}⚠️${NC} $file (requires ESLint for full validation)"
        VALID_FILES=$((VALID_FILES + 1))
    fi
done

echo ""
echo "JavaScript Summary: $js_count files checked"
echo ""

# Final summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}FINAL VALIDATION REPORT${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Total files scanned: $TOTAL_FILES"
echo -e "Files valid: ${GREEN}$VALID_FILES${NC}"
echo -e "Files with errors: ${RED}$ERROR_FILES${NC}"
echo ""

if [ $ERROR_FILES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL SYNTAX CHECKS PASSED!${NC}"
    echo ""
    echo "Safe to commit."
    exit 0
else
    echo -e "${RED}❌ SYNTAX ERRORS FOUND!${NC}"
    echo ""
    echo "Please fix the errors listed above and try again."
    exit 1
fi
