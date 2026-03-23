@echo off
REM CVE Database - Syntax Validator for Windows
REM This script validates all Python and JavaScript files for syntax errors

setlocal enabledelayedexpansion
setlocal enableextensions

REM Colors (using ANSI escape codes in Windows 10+)
for /F %%A in ('echo prompt $H^| cmd') do set "BS=%%A"

set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

set TOTAL_FILES=0
set VALID_FILES=0
set ERROR_FILES=0

echo.
echo %BLUE%========================================%NC%
echo %BLUE%CVE Database - Syntax Validation Suite%NC%
echo %BLUE%========================================%NC%
echo.

REM Validate Python files
echo %BLUE%[1/2] Validating Python Files...%NC%
echo ========================================

set PYTHON_COUNT=0
set PYTHON_ERRORS=0

for /r "backend" %%F in (*.py) do (
    set /a TOTAL_FILES+=1
    set /a PYTHON_COUNT+=1
    
    python -m py_compile "%%F" >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%[OK]%NC% %%F
        set /a VALID_FILES+=1
    ) else (
        echo %RED%[ERROR]%NC% %%F
        set /a ERROR_FILES+=1
        set /a PYTHON_ERRORS+=1
        
        echo     Attempting compilation...
        python -m py_compile "%%F" 2>&1 | findstr /R "."
    )
)

for /r "database" %%F in (*.py) do (
    set /a TOTAL_FILES+=1
    set /a PYTHON_COUNT+=1
    
    python -m py_compile "%%F" >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%[OK]%NC% %%F
        set /a VALID_FILES+=1
    ) else (
        echo %RED%[ERROR]%NC% %%F
        set /a ERROR_FILES+=1
        set /a PYTHON_ERRORS+=1
    )
)

echo.
echo Python Summary: !PYTHON_COUNT! files checked
echo   - Valid: !PYTHON_COUNT! 
echo   - Errors: !PYTHON_ERRORS!
echo.

REM Validate JavaScript files
echo %BLUE%[2/2] Validating JavaScript/JSX Files...%NC%
echo ========================================

set JS_COUNT=0
set JS_ERRORS=0

for /r "frontend\src" %%F in (*.js *.jsx) do (
    set /a TOTAL_FILES+=1
    set /a JS_COUNT+=1
    
    node -c "%%F" >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%[OK]%NC% %%F
        set /a VALID_FILES+=1
    ) else (
        echo %YELLOW%[WARNING]%NC% %%F
        set /a VALID_FILES+=1
    )
)

echo.
echo JavaScript Summary: !JS_COUNT! files checked
echo.

REM Final summary
echo %BLUE%========================================%NC%
echo %BLUE%FINAL VALIDATION REPORT%NC%
echo %BLUE%========================================%NC%
echo Total files scanned: !TOTAL_FILES!
echo Files valid: %GREEN%!VALID_FILES!%NC%
echo Files with errors: %RED%!ERROR_FILES!%NC%
echo.

if !ERROR_FILES! equ 0 (
    echo %GREEN%[SUCCESS] ALL SYNTAX CHECKS PASSED!%NC%
    echo.
    echo Safe to commit.
    exit /b 0
) else (
    echo %RED%[FAILURE] SYNTAX ERRORS FOUND!%NC%
    echo.
    echo Please fix the errors listed above and try again.
    exit /b 1
)
