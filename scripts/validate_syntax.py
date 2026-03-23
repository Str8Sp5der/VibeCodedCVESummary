#!/usr/bin/env python3
"""
CVE Database - Comprehensive Syntax Validator
Validates all Python and JavaScript files for syntax errors
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# Color codes
class Color(Enum):
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message: str, color: Color = Color.RESET):
    """Print colored message"""
    print(f"{color.value}{message}{Color.RESET.value}")

def print_header(text: str):
    """Print formatted header"""
    print()
    print_colored("=" * 50, Color.BLUE)
    print_colored(text, Color.BLUE)
    print_colored("=" * 50, Color.BLUE)
    print()

@dataclass
class ValidationResult:
    """Result of file validation"""
    file_path: str
    is_valid: bool
    error_message: str = ""
    file_type: str = "unknown"

class PythonValidator:
    """Validates Python files"""
    
    @staticmethod
    def get_python_files() -> List[Path]:
        """Get all Python files in backend and database directories"""
        files = []
        for pattern in ['backend/**/*.py', 'database/**/*.py']:
            files.extend(Path('.').glob(pattern))
        return sorted(files)
    
    @staticmethod
    def validate(file_path: Path) -> ValidationResult:
        """Validate Python file syntax"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), str(file_path), 'exec')
            return ValidationResult(str(file_path), True, file_type='Python')
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            return ValidationResult(str(file_path), False, error_msg, file_type='Python')
        except Exception as e:
            return ValidationResult(str(file_path), False, str(e), file_type='Python')

class JavaScriptValidator:
    """Validates JavaScript files"""
    
    @staticmethod
    def get_javascript_files() -> List[Path]:
        """Get all JavaScript files in frontend directory"""
        files = []
        for pattern in ['frontend/src/**/*.js', 'frontend/src/**/*.jsx', 'frontend/*.js']:
            files.extend(Path('.').glob(pattern))
        return sorted(files)
    
    @staticmethod
    def validate(file_path: Path) -> ValidationResult:
        """Validate JavaScript file syntax using Node.js"""
        try:
            result = subprocess.run(
                ['node', '-c', str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ValidationResult(str(file_path), True, file_type='JavaScript')
            else:
                return ValidationResult(str(file_path), False, result.stderr, file_type='JavaScript')
        except FileNotFoundError:
            return ValidationResult(str(file_path), True, "Node.js not found (skipping)", file_type='JavaScript')
        except subprocess.TimeoutExpired:
            return ValidationResult(str(file_path), False, "Validation timeout", file_type='JavaScript')
        except Exception as e:
            return ValidationResult(str(file_path), False, str(e), file_type='JavaScript')

class SyntaxValidator:
    """Main syntax validator"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.stats = {
            'total': 0,
            'valid': 0,
            'errors': 0,
            'by_type': {}
        }
    
    def validate_all(self):
        """Validate all files"""
        print_header("CVE Database - Syntax Validation Suite")
        
        # Validate Python files
        self._validate_file_type("Python", PythonValidator)
        
        # Validate JavaScript files
        self._validate_file_type("JavaScript", JavaScriptValidator)
        
        # Print summary
        self._print_summary()
    
    def _validate_file_type(self, type_name: str, validator_class):
        """Validate files of specific type"""
        print_colored(f"[1] Validating {type_name} Files...", Color.BLUE)
        print("=" * 50)
        
        if type_name == "Python":
            files = validator_class.get_python_files()
        else:
            files = validator_class.get_javascript_files()
        
        type_results = []
        type_errors = []
        
        for file_path in files:
            self.stats['total'] += 1
            
            result = validator_class.validate(file_path)
            self.results.append(result)
            
            if result.is_valid:
                status = "✅" if "skip" not in result.error_message.lower() else "⚠️"
                print_colored(f"{status} {result.file_path}", Color.GREEN)
                self.stats['valid'] += 1
                type_results.append(result)
            else:
                print_colored(f"❌ {result.file_path}", Color.RED)
                if result.error_message:
                    print(f"   Error: {result.error_message}")
                self.stats['errors'] += 1
                type_errors.append(result)
                type_results.append(result)
        
        self.stats['by_type'][type_name] = {
            'total': len(files),
            'valid': self.stats['valid'],
            'errors': len(type_errors)
        }
        
        print()
        print(f"{type_name} Summary: {len(files)} files checked")
        print(f"  - Valid: {len(files) - len(type_errors)}")
        print(f"  - Errors: {len(type_errors)}")
        print()
    
    def _print_summary(self):
        """Print final validation summary"""
        print_header("FINAL VALIDATION REPORT")
        
        print(f"Total files scanned: {self.stats['total']}")
        print_colored(f"Files valid: {self.stats['valid']}", Color.GREEN)
        print_colored(f"Files with errors: {self.stats['errors']}", Color.RED)
        
        print()
        print("Breakdown by type:")
        for file_type, stats in self.stats['by_type'].items():
            print(f"  {file_type}: {stats['valid']}/{stats['total']} valid")
        
        print()
        
        if self.stats['errors'] == 0:
            print_colored("✅ ALL SYNTAX CHECKS PASSED!", Color.GREEN)
            print()
            print("Safe to commit.")
            return 0
        else:
            print_colored("❌ SYNTAX ERRORS FOUND!", Color.RED)
            print()
            print("Please fix the errors listed above and try again.")
            return 1
    
    def run(self):
        """Run validator and exit with appropriate code"""
        self.validate_all()
        exit_code = 0 if self.stats['errors'] == 0 else 1
        sys.exit(exit_code)

def main():
    """Main entry point"""
    try:
        # Change to project root
        if not Path('backend').exists():
            print_colored("Error: Could not find project root (backend directory missing)", Color.RED)
            sys.exit(1)
        
        validator = SyntaxValidator()
        validator.run()
    except KeyboardInterrupt:
        print_colored("\nValidation interrupted by user", Color.YELLOW)
        sys.exit(130)
    except Exception as e:
        print_colored(f"Error during validation: {e}", Color.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()
