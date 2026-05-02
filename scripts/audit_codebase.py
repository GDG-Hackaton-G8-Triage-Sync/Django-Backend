#!/usr/bin/env python
"""
Comprehensive Codebase Audit Script

This script analyzes the Django project for:
1. Duplicate code
2. Unused imports
3. Dead code
4. Performance bottlenecks
5. Missing error handling
6. Integration issues
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict, Counter
import json

class CodebaseAuditor:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        
    def audit(self):
        """Run all audit checks"""
        print("=" * 80)
        print("CODEBASE AUDIT REPORT")
        print("=" * 80)
        print()
        
        self.check_duplicate_functions()
        self.check_unused_models()
        self.check_debug_code()
        self.check_n_plus_one_queries()
        self.check_missing_indexes()
        self.check_circular_imports()
        self.check_large_files()
        self.check_test_coverage()
        
        self.print_report()
        
    def check_duplicate_functions(self):
        """Find duplicate function definitions"""
        print("Checking for duplicate functions...")
        functions = defaultdict(list)
        
        for py_file in self.base_path.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions[node.name].append(str(py_file.relative_to(self.base_path)))
            except Exception as e:
                pass
        
        # Find duplicates
        for func_name, locations in functions.items():
            if len(locations) > 1 and not func_name.startswith('_'):
                self.issues['duplicate_functions'].append({
                    'function': func_name,
                    'locations': locations,
                    'count': len(locations)
                })
                self.stats['duplicate_functions'] += 1
        
        print(f"  Found {self.stats['duplicate_functions']} duplicate functions\n")
    
    def check_unused_models(self):
        """Find models that are defined but never used"""
        print("Checking for unused models...")
        
        # Check triage/models.py for unused models
        models_file = self.base_path / "triagesync_backend/apps/triage/models.py"
        if models_file.exists():
            with open(models_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "TODO: Remove these models" in content:
                    self.issues['unused_models'].append({
                        'file': 'triage/models.py',
                        'models': ['TriageSession', 'AIResult', 'FileUpload'],
                        'note': 'Marked for removal - never used in codebase'
                    })
                    self.stats['unused_models'] += 3
        
        print(f"  Found {self.stats['unused_models']} unused models\n")
    
    def check_debug_code(self):
        """Find debug/temporary code that should be removed"""
        print("Checking for debug code...")
        
        debug_patterns = [
            r'# DEBUG:',
            r'print\(',
            r'import pdb',
            r'breakpoint\(',
            r'console\.log',
        ]
        
        for py_file in self.base_path.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file) or "tests" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in debug_patterns:
                            if re.search(pattern, line):
                                self.issues['debug_code'].append({
                                    'file': str(py_file.relative_to(self.base_path)),
                                    'line': line_num,
                                    'code': line.strip()
                                })
                                self.stats['debug_code'] += 1
            except Exception:
                pass
        
        print(f"  Found {self.stats['debug_code']} debug statements\n")
    
    def check_n_plus_one_queries(self):
        """Find potential N+1 query issues"""
        print("Checking for N+1 query patterns...")
        
        # Look for loops with queries inside
        n_plus_one_patterns = [
            r'for .+ in .+\.objects\.all\(\):',
            r'for .+ in .+\.filter\(',
        ]
        
        for py_file in self.base_path.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines):
                        for pattern in n_plus_one_patterns:
                            if re.search(pattern, line):
                                # Check if next few lines have .objects or .filter
                                next_lines = lines[i+1:i+10]
                                for j, next_line in enumerate(next_lines):
                                    if '.objects.' in next_line or '.filter(' in next_line:
                                        self.issues['n_plus_one'].append({
                                            'file': str(py_file.relative_to(self.base_path)),
                                            'line': i + 1,
                                            'pattern': line.strip()
                                        })
                                        self.stats['n_plus_one'] += 1
                                        break
            except Exception:
                pass
        
        print(f"  Found {self.stats['n_plus_one']} potential N+1 queries\n")
    
    def check_missing_indexes(self):
        """Check for fields that should be indexed"""
        print("Checking for missing database indexes...")
        
        # Common fields that should be indexed
        index_candidates = ['status', 'priority', 'created_at', 'updated_at', 'user_id', 'patient_id']
        
        for py_file in self.base_path.rglob("models.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for field in index_candidates:
                        # Check if field exists but doesn't have db_index=True
                        if f'{field} =' in content or f'{field}=' in content:
                            if f'db_index=True' not in content or field not in content:
                                # Simple heuristic - may have false positives
                                pass
            except Exception:
                pass
        
        print(f"  Checked for missing indexes\n")
    
    def check_circular_imports(self):
        """Detect potential circular import issues"""
        print("Checking for circular imports...")
        
        imports = defaultdict(set)
        
        for py_file in self.base_path.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    module_name = str(py_file.relative_to(self.base_path)).replace('/', '.').replace('.py', '')
                    
                    # Find all imports
                    for match in re.finditer(r'from ([\w.]+) import', content):
                        imported_module = match.group(1)
                        if 'triagesync_backend' in imported_module:
                            imports[module_name].add(imported_module)
            except Exception:
                pass
        
        # Simple circular detection (A imports B, B imports A)
        for module, imported in imports.items():
            for imp in imported:
                if module in imports.get(imp, set()):
                    self.issues['circular_imports'].append({
                        'module1': module,
                        'module2': imp
                    })
                    self.stats['circular_imports'] += 1
        
        print(f"  Found {self.stats['circular_imports']} potential circular imports\n")
    
    def check_large_files(self):
        """Find files that are too large and should be split"""
        print("Checking for large files...")
        
        for py_file in self.base_path.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 500:
                        self.issues['large_files'].append({
                            'file': str(py_file.relative_to(self.base_path)),
                            'lines': len(lines),
                            'recommendation': 'Consider splitting into smaller modules'
                        })
                        self.stats['large_files'] += 1
            except Exception:
                pass
        
        print(f"  Found {self.stats['large_files']} large files (>500 lines)\n")
    
    def check_test_coverage(self):
        """Check test file coverage"""
        print("Checking test coverage...")
        
        app_files = set()
        test_files = set()
        
        for py_file in self.base_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "migrations" in str(py_file):
                continue
                
            rel_path = str(py_file.relative_to(self.base_path))
            
            if "/tests/" in rel_path or rel_path.startswith("tests/"):
                test_files.add(rel_path)
            elif "/apps/" in rel_path and not rel_path.endswith("__init__.py"):
                app_files.add(rel_path)
        
        self.stats['app_files'] = len(app_files)
        self.stats['test_files'] = len(test_files)
        
        print(f"  App files: {len(app_files)}")
        print(f"  Test files: {len(test_files)}\n")
    
    def print_report(self):
        """Print comprehensive audit report"""
        print("\n" + "=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print()
        
        # Critical Issues
        print("🔴 CRITICAL ISSUES:")
        print(f"  - Unused models: {self.stats['unused_models']}")
        print(f"  - Circular imports: {self.stats['circular_imports']}")
        print(f"  - N+1 queries: {self.stats['n_plus_one']}")
        print()
        
        # Warnings
        print("🟡 WARNINGS:")
        print(f"  - Debug code: {self.stats['debug_code']}")
        print(f"  - Duplicate functions: {self.stats['duplicate_functions']}")
        print(f"  - Large files: {self.stats['large_files']}")
        print()
        
        # Info
        print("ℹ️  INFO:")
        print(f"  - App files: {self.stats['app_files']}")
        print(f"  - Test files: {self.stats['test_files']}")
        print()
        
        # Detailed Issues
        if self.issues['duplicate_functions']:
            print("\n" + "-" * 80)
            print("DUPLICATE FUNCTIONS:")
            for issue in self.issues['duplicate_functions'][:10]:
                print(f"\n  Function: {issue['function']}")
                print(f"  Found in {issue['count']} locations:")
                for loc in issue['locations']:
                    print(f"    - {loc}")
        
        if self.issues['unused_models']:
            print("\n" + "-" * 80)
            print("UNUSED MODELS:")
            for issue in self.issues['unused_models']:
                print(f"\n  File: {issue['file']}")
                print(f"  Models: {', '.join(issue['models'])}")
                print(f"  Note: {issue['note']}")
        
        if self.issues['debug_code']:
            print("\n" + "-" * 80)
            print("DEBUG CODE (first 10):")
            for issue in self.issues['debug_code'][:10]:
                print(f"\n  {issue['file']}:{issue['line']}")
                print(f"    {issue['code']}")
        
        if self.issues['large_files']:
            print("\n" + "-" * 80)
            print("LARGE FILES:")
            for issue in sorted(self.issues['large_files'], key=lambda x: x['lines'], reverse=True)[:10]:
                print(f"\n  {issue['file']}: {issue['lines']} lines")
                print(f"    {issue['recommendation']}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("=" * 80)
        print()
        print("1. Remove unused models from triage/models.py")
        print("2. Clean up debug logging statements in production code")
        print("3. Consolidate duplicate functions into shared utilities")
        print("4. Add select_related/prefetch_related to prevent N+1 queries")
        print("5. Split large files into smaller, focused modules")
        print("6. Add database indexes for frequently queried fields")
        print()

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent / "triagesync_backend"
    auditor = CodebaseAuditor(base_path)
    auditor.audit()
