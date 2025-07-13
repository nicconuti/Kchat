#!/usr/bin/env python3
"""
Analyze unused code in the Python files
"""

import ast
import os
import re
from collections import defaultdict

def analyze_codebase():
    """Analyze the codebase for unused methods, functions, and variables"""
    
    # Get all Python files excluding Kchat directory
    py_files = []
    for root, dirs, files in os.walk('.'):
        if 'Kchat' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    
    print(f"Analyzing {len(py_files)} Python files...")
    
    # Track definitions and usages
    defined_functions = {}
    defined_classes = {}
    function_calls = set()
    method_calls = set()
    class_usage = set()
    imports = set()
    
    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Find definitions and usages
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip magic methods and private methods for now
                    if not node.name.startswith('__'):
                        defined_functions[f'{file_path}:{node.name}'] = {
                            'line': node.lineno,
                            'file': file_path,
                            'name': node.name
                        }
                
                elif isinstance(node, ast.ClassDef):
                    defined_classes[f'{file_path}:{node.name}'] = {
                        'line': node.lineno,
                        'file': file_path,
                        'name': node.name
                    }
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        function_calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        method_calls.add(node.func.attr)
                        if isinstance(node.func.value, ast.Name):
                            class_usage.add(node.func.value.id)
                
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    class_usage.add(node.id)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.add(alias.name)
        
        except Exception as e:
            print(f'Error parsing {file_path}: {e}')
    
    return analyze_unused(defined_functions, defined_classes, function_calls, method_calls, class_usage)

def analyze_unused(defined_functions, defined_classes, function_calls, method_calls, class_usage):
    """Analyze what's unused"""
    
    unused_functions = []
    unused_classes = []
    potentially_unused_methods = []
    
    # Check functions
    for func_key, func_info in defined_functions.items():
        func_name = func_info['name']
        
        # Skip main functions and special cases
        if func_name in ['main', 'setup_logging', '__init__']:
            continue
        
        # Check if function is called anywhere
        if func_name not in function_calls and func_name not in method_calls:
            # Special handling for methods vs functions
            if func_name.startswith('_') and not func_name.startswith('__'):
                potentially_unused_methods.append(func_info)
            else:
                unused_functions.append(func_info)
    
    # Check classes
    for class_key, class_info in defined_classes.items():
        class_name = class_info['name']
        
        if class_name not in class_usage:
            unused_classes.append(class_info)
    
    return unused_functions, unused_classes, potentially_unused_methods

def find_dead_code_patterns():
    """Find common dead code patterns"""
    
    dead_code_issues = []
    
    py_files = []
    for root, dirs, files in os.walk('.'):
        if 'Kchat' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    
    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Look for unreachable code after return
                if line_stripped.startswith('return ') and i < len(lines):
                    next_lines = []
                    for j in range(i, min(i + 3, len(lines))):
                        if j < len(lines):
                            next_line = lines[j].strip()
                            if next_line and not next_line.startswith('#') and not next_line.startswith('def ') and not next_line.startswith('class '):
                                next_lines.append((j + 1, next_line))
                    
                    if next_lines:
                        dead_code_issues.append({
                            'file': file_path,
                            'line': i,
                            'type': 'unreachable_after_return',
                            'details': f"Return at line {i}, unreachable code: {next_lines[0][1][:50]}..."
                        })
                
                # Look for duplicate imports
                if line_stripped.startswith('import ') or line_stripped.startswith('from '):
                    # Check if import appears multiple times
                    import_count = sum(1 for l in lines if l.strip() == line_stripped)
                    if import_count > 1:
                        dead_code_issues.append({
                            'file': file_path,
                            'line': i,
                            'type': 'duplicate_import',
                            'details': f"Import '{line_stripped}' appears {import_count} times"
                        })
                
                # Look for TODO/FIXME/PLACEHOLDER comments
                if any(marker in line_stripped.upper() for marker in ['TODO', 'FIXME', 'PLACEHOLDER', 'HACK']):
                    dead_code_issues.append({
                        'file': file_path,
                        'line': i,
                        'type': 'technical_debt',
                        'details': line_stripped
                    })
        
        except Exception as e:
            print(f'Error analyzing {file_path}: {e}')
    
    return dead_code_issues

def main():
    print("=== UNUSED CODE ANALYSIS ===\n")
    
    unused_functions, unused_classes, potentially_unused_methods = analyze_codebase()
    
    print("=== UNUSED FUNCTIONS ===")
    if unused_functions:
        for func in unused_functions[:15]:  # Limit output
            print(f"  {func['file']}:{func['line']} - {func['name']}()")
        if len(unused_functions) > 15:
            print(f"  ... and {len(unused_functions) - 15} more")
    else:
        print("  No unused functions found")
    
    print(f"\n=== UNUSED CLASSES ===")
    if unused_classes:
        for cls in unused_classes:
            print(f"  {cls['file']}:{cls['line']} - class {cls['name']}")
    else:
        print("  No unused classes found")
    
    print(f"\n=== POTENTIALLY UNUSED PRIVATE METHODS ===")
    if potentially_unused_methods:
        for method in potentially_unused_methods[:10]:  # Limit output
            print(f"  {method['file']}:{method['line']} - {method['name']}()")
        if len(potentially_unused_methods) > 10:
            print(f"  ... and {len(potentially_unused_methods) - 10} more")
    else:
        print("  No potentially unused private methods found")
    
    print(f"\n=== DEAD CODE PATTERNS ===")
    dead_code_issues = find_dead_code_patterns()
    
    # Group by type
    by_type = defaultdict(list)
    for issue in dead_code_issues:
        by_type[issue['type']].append(issue)
    
    for issue_type, issues in by_type.items():
        print(f"\n{issue_type.replace('_', ' ').title()}:")
        for issue in issues[:5]:  # Limit per type
            print(f"  {issue['file']}:{issue['line']} - {issue['details']}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Unused functions: {len(unused_functions)}")
    print(f"Unused classes: {len(unused_classes)}")
    print(f"Potentially unused private methods: {len(potentially_unused_methods)}")
    print(f"Dead code issues: {len(dead_code_issues)}")

if __name__ == "__main__":
    main()