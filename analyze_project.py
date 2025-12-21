#!/usr/bin/env python3
"""
Comprehensive project analysis script for SAS Management System.
Scans all blueprints, routes, templates, and identifies missing endpoints.
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent
SAS_MANAGEMENT = PROJECT_ROOT / "sas_management"
BLUEPRINTS_DIR = SAS_MANAGEMENT / "blueprints"
TEMPLATES_DIR = SAS_MANAGEMENT / "templates"
HIRE_DIR = SAS_MANAGEMENT / "hire"

class BlueprintAnalyzer:
    def __init__(self):
        self.blueprints: Dict[str, Dict] = {}
        self.endpoints: Dict[str, Set[str]] = defaultdict(set)
        self.template_urls: Set[str] = set()
        self.navigation_urls: Set[str] = set()
        self.missing_endpoints: List[Tuple[str, str]] = []
        
    def extract_blueprint_info(self, file_path: Path) -> Dict:
        """Extract blueprint name and URL prefix from __init__.py or routes.py"""
        info = {"name": None, "url_prefix": None, "file": str(file_path)}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find Blueprint definition
            blueprint_match = re.search(
                r'(\w+)\s*=\s*Blueprint\(["\'](\w+)["\']\s*,\s*__name__\s*(?:,\s*url_prefix=["\']([^"\']+)["\'])?',
                content
            )
            
            if blueprint_match:
                var_name = blueprint_match.group(1)
                blueprint_name = blueprint_match.group(2)
                url_prefix = blueprint_match.group(3) if blueprint_match.group(3) else None
                
                info["name"] = blueprint_name
                info["url_prefix"] = url_prefix
                info["var_name"] = var_name
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return info
    
    def extract_routes_from_file(self, file_path: Path, blueprint_name: str) -> Set[str]:
        """Extract all route endpoints from a Python file"""
        routes = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to find route decorators
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Call):
                                if isinstance(decorator.func, ast.Attribute):
                                    if decorator.func.attr == 'route':
                                        # Extract route path
                                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                            route_path = decorator.args[0].value
                                            routes.add((node.name, route_path))
                                        elif decorator.args and isinstance(decorator.args[0], ast.Str):
                                            route_path = decorator.args[0].s
                                            routes.add((node.name, route_path))
            except SyntaxError:
                # Fallback to regex if AST parsing fails
                route_pattern = r'@\w+\.route\(["\']([^"\']+)["\']'
                matches = re.findall(route_pattern, content)
                for match in matches:
                    # Try to find function name
                    func_pattern = rf'@\w+\.route\(["\']{re.escape(match)}["\']\s*.*?\ndef\s+(\w+)'
                    func_match = re.search(func_pattern, content, re.DOTALL)
                    if func_match:
                        routes.add((func_match.group(1), match))
                    else:
                        routes.add(('unknown', match))
                        
        except Exception as e:
            print(f"Error extracting routes from {file_path}: {e}")
            
        return routes
    
    def extract_url_for_from_template(self, file_path: Path) -> Set[str]:
        """Extract all url_for references from a template"""
        urls = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all url_for calls
            pattern = r"url_for\(['\"](\w+)\.(\w+)['\"]"
            matches = re.findall(pattern, content)
            for blueprint, endpoint in matches:
                urls.add(f"{blueprint}.{endpoint}")
                
        except Exception as e:
            print(f"Error reading template {file_path}: {e}")
            
        return urls
    
    def scan_blueprints(self):
        """Scan all blueprint directories"""
        print("Scanning blueprints...")
        
        # Scan blueprints directory
        if BLUEPRINTS_DIR.exists():
            for blueprint_dir in sorted(BLUEPRINTS_DIR.iterdir()):
                if blueprint_dir.is_dir() and not blueprint_dir.name.startswith('_'):
                    self.scan_blueprint_directory(blueprint_dir)
        
        # Scan hire directory (special case)
        if HIRE_DIR.exists():
            self.scan_hire_directory()
    
    def scan_blueprint_directory(self, blueprint_dir: Path):
        """Scan a single blueprint directory"""
        blueprint_name = blueprint_dir.name
        
        # Find __init__.py or routes.py
        init_file = blueprint_dir / "__init__.py"
        routes_file = blueprint_dir / "routes.py"
        
        info = {}
        if init_file.exists():
            info = self.extract_blueprint_info(init_file)
        elif routes_file.exists():
            info = self.extract_blueprint_info(routes_file)
        
        if not info.get("name"):
            info["name"] = blueprint_name
        
        # Extract routes from all Python files
        routes = set()
        for py_file in blueprint_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                file_routes = self.extract_routes_from_file(py_file, blueprint_name)
                routes.update(file_routes)
        
        info["routes"] = routes
        info["endpoints"] = {func_name for func_name, _ in routes}
        
        self.blueprints[blueprint_name] = info
        
        # Store endpoints with blueprint prefix
        for func_name, route_path in routes:
            endpoint_name = f"{blueprint_name}.{func_name}"
            self.endpoints[blueprint_name].add(endpoint_name)
    
    def scan_hire_directory(self):
        """Scan the hire directory (special case)"""
        if not HIRE_DIR.exists():
            return
            
        info = self.extract_blueprint_info(HIRE_DIR / "__init__.py")
        if not info.get("name"):
            info["name"] = "hire"
        info["url_prefix"] = "/hire"
        
        # Extract routes
        routes_file = HIRE_DIR / "routes.py"
        routes = set()
        if routes_file.exists():
            routes = self.extract_routes_from_file(routes_file, "hire")
        
        # Check maintenance routes
        maintenance_file = BLUEPRINTS_DIR / "hire" / "maintenance_routes.py"
        if maintenance_file.exists():
            maintenance_routes = self.extract_routes_from_file(maintenance_file, "maintenance")
            routes.update(maintenance_routes)
        
        info["routes"] = routes
        info["endpoints"] = {func_name for func_name, _ in routes}
        
        self.blueprints["hire"] = info
        
        for func_name, route_path in routes:
            endpoint_name = f"hire.{func_name}"
            self.endpoints["hire"].add(endpoint_name)
    
    def scan_templates(self):
        """Scan all templates for url_for references"""
        print("Scanning templates...")
        
        if not TEMPLATES_DIR.exists():
            return
        
        for template_file in TEMPLATES_DIR.rglob("*.html"):
            urls = self.extract_url_for_from_template(template_file)
            self.template_urls.update(urls)
    
    def scan_routes_py(self):
        """Scan routes.py for navigation endpoints"""
        print("Scanning routes.py for navigation...")
        
        routes_file = SAS_MANAGEMENT / "routes.py"
        if routes_file.exists():
            try:
                with open(routes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find url_for calls
                pattern = r"url_for\(['\"](\w+)\.(\w+)['\"]"
                matches = re.findall(pattern, content)
                for blueprint, endpoint in matches:
                    self.navigation_urls.add(f"{blueprint}.{endpoint}")
                    
            except Exception as e:
                print(f"Error reading routes.py: {e}")
    
    def compare_endpoints(self):
        """Compare template/navigation URLs against available endpoints"""
        print("Comparing endpoints...")
        
        all_available = set()
        for blueprint, endpoints in self.endpoints.items():
            all_available.update(endpoints)
        
        # Check template URLs
        for url in self.template_urls:
            if url not in all_available:
                self.missing_endpoints.append(("template", url))
        
        # Check navigation URLs
        for url in self.navigation_urls:
            if url not in all_available:
                self.missing_endpoints.append(("navigation", url))
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 80)
        report.append("SAS MANAGEMENT SYSTEM - COMPREHENSIVE PROJECT ANALYSIS")
        report.append("=" * 80)
        report.append("")
        
        # Blueprints Summary
        report.append("1. BLUEPRINT ANALYSIS")
        report.append("-" * 80)
        report.append("")
        
        for blueprint_name, info in sorted(self.blueprints.items()):
            report.append(f"Blueprint: {blueprint_name}")
            report.append(f"  URL Prefix: {info.get('url_prefix', 'None')}")
            report.append(f"  File: {info.get('file', 'N/A')}")
            report.append(f"  Endpoints ({len(info.get('endpoints', set()))}):")
            
            endpoints = sorted(info.get('endpoints', set()))
            for endpoint in endpoints:
                # Find route path
                route_path = "?"
                for func_name, path in info.get('routes', set()):
                    if func_name == endpoint.split('.')[-1]:
                        route_path = path
                        break
                report.append(f"    - {endpoint} -> {route_path}")
            
            report.append("")
        
        # Missing Endpoints
        report.append("2. MISSING ENDPOINTS")
        report.append("-" * 80)
        report.append("")
        
        if self.missing_endpoints:
            by_source = defaultdict(list)
            for source, endpoint in self.missing_endpoints:
                by_source[source].append(endpoint)
            
            for source in sorted(by_source.keys()):
                report.append(f"{source.upper()} References:")
                for endpoint in sorted(by_source[source]):
                    report.append(f"  - {endpoint}")
                report.append("")
        else:
            report.append("No missing endpoints found!")
            report.append("")
        
        # Template URL Summary
        report.append("3. TEMPLATE URL REFERENCES")
        report.append("-" * 80)
        report.append(f"Total unique url_for references: {len(self.template_urls)}")
        report.append("")
        
        # Navigation URL Summary
        report.append("4. NAVIGATION URL REFERENCES (from routes.py)")
        report.append("-" * 80)
        report.append(f"Total unique url_for references: {len(self.navigation_urls)}")
        report.append("")
        
        # Hire Module Specific Analysis
        report.append("5. HIRE MODULE SPECIFIC ANALYSIS")
        report.append("-" * 80)
        hire_info = self.blueprints.get("hire", {})
        report.append(f"Blueprint: hire")
        report.append(f"  URL Prefix: {hire_info.get('url_prefix', 'None')}")
        report.append(f"  Defined Endpoints: {sorted(hire_info.get('endpoints', set()))}")
        
        # Check for hire.inventory_list specifically
        if "hire.inventory_list" not in self.endpoints.get("hire", set()):
            report.append("  ⚠️  MISSING: hire.inventory_list")
        if "hire.inventory_add" not in self.endpoints.get("hire", set()):
            report.append("  ⚠️  MISSING: hire.inventory_add")
        if "hire.inventory_edit" not in self.endpoints.get("hire", set()):
            report.append("  ⚠️  MISSING: hire.inventory_edit")
        if "hire.inventory_delete" not in self.endpoints.get("hire", set()):
            report.append("  ⚠️  MISSING: hire.inventory_delete")
        
        report.append("")
        
        # Summary Statistics
        report.append("6. SUMMARY STATISTICS")
        report.append("-" * 80)
        report.append(f"Total Blueprints: {len(self.blueprints)}")
        report.append(f"Total Endpoints: {sum(len(eps) for eps in self.endpoints.values())}")
        report.append(f"Total Template URLs: {len(self.template_urls)}")
        report.append(f"Total Navigation URLs: {len(self.navigation_urls)}")
        report.append(f"Missing Endpoints: {len(self.missing_endpoints)}")
        report.append("")
        
        return "\n".join(report)

def main():
    analyzer = BlueprintAnalyzer()
    
    print("Starting comprehensive project analysis...")
    print("")
    
    analyzer.scan_blueprints()
    analyzer.scan_templates()
    analyzer.scan_routes_py()
    analyzer.compare_endpoints()
    
    report = analyzer.generate_report()
    
    # Print to console
    print(report)
    
    # Save to file
    output_file = PROJECT_ROOT / "PROJECT_ANALYSIS_REPORT.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport saved to: {output_file}")

if __name__ == "__main__":
    main()


