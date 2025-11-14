"""
Project Map Generator - Analyse AST complète du projet

Génère un fichier project-map.json contenant :
- Structure complète du projet
- Imports/exports Python (analyse AST)
- Routes API détectées
- Métriques (lignes de code, complexité cyclomatique)
- Graphe de dépendances
"""

import ast
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Any, Optional
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class PythonFileAnalyzer(ast.NodeVisitor):
    """Analyze Python file using AST"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.imports: List[Dict[str, str]] = []
        self.exports: List[str] = []
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.routes: List[Dict[str, Any]] = []
        self.complexity = 0
        
    def visit_Import(self, node: ast.Import):
        """Visit import statement"""
        for alias in node.names:
            self.imports.append({
                "type": "import",
                "module": alias.name,
                "alias": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from...import statement"""
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "type": "from_import",
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition"""
        # Check if it's an API route
        is_route = False
        route_info = None
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr'):
                    method = decorator.func.attr
                    if method in ['get', 'post', 'put', 'delete', 'patch']:
                        is_route = True
                        path = ""
                        if decorator.args:
                            if isinstance(decorator.args[0], ast.Constant):
                                path = decorator.args[0].value
                        
                        route_info = {
                            "method": method.upper(),
                            "path": path,
                            "function": node.name,
                            "line": node.lineno
                        }
        
        if is_route and route_info:
            self.routes.append(route_info)
        
        # Function info
        self.functions.append({
            "name": node.name,
            "line": node.lineno,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "args": [arg.arg for arg in node.args.args],
            "decorators": len(node.decorator_list)
        })
        
        # Calculate complexity (simplified McCabe)
        self.complexity += self._calculate_complexity(node)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition"""
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition"""
        self.classes.append({
            "name": node.name,
            "line": node.lineno,
            "bases": [self._get_name(base) for base in node.bases],
            "methods": []
        })
        
        # Add to exports if it's a model/schema
        if any(base_name in ['SQLModel', 'BaseModel', 'Enum'] 
               for base_name in [self._get_name(base) for base in node.bases]):
            self.exports.append(node.name)
        
        self.generic_visit(node)
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)


def analyze_python_file(filepath: Path) -> Dict[str, Any]:
    """Analyze a Python file and extract information"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.count('\n') + 1
        
        # Parse AST
        tree = ast.parse(content, filename=str(filepath))
        
        # Analyze
        analyzer = PythonFileAnalyzer(str(filepath))
        analyzer.visit(tree)
        
        return {
            "path": str(filepath.relative_to(Path.cwd())),
            "lines": lines,
            "imports": analyzer.imports,
            "exports": analyzer.exports,
            "functions": analyzer.functions,
            "classes": analyzer.classes,
            "routes": analyzer.routes,
            "complexity": analyzer.complexity
        }
    
    except Exception as e:
        print(f"Erreur lors de l'analyse de {filepath}: {e}")
        return {
            "path": str(filepath.relative_to(Path.cwd())),
            "error": str(e)
        }


def scan_project(root_path: Path) -> Dict[str, Any]:
    """Scan the entire project"""
    
    print("Scan du projet...")
    
    # Find all Python files
    python_files = []
    exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.pytest_cache'}
    
    for py_file in root_path.rglob('*.py'):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue
        python_files.append(py_file)
    
    print(f"Trouve {len(python_files)} fichiers Python")
    
    # Analyze files
    files_data = []
    total_lines = 0
    total_complexity = 0
    
    for py_file in python_files:
        print(f"   Analyse: {py_file.relative_to(root_path)}")
        file_data = analyze_python_file(py_file)
        
        if 'error' not in file_data:
            files_data.append(file_data)
            total_lines += file_data['lines']
            total_complexity += file_data['complexity']
    
    # Group by modules
    modules = defaultdict(lambda: {
        "name": "",
        "type": "module",
        "files": [],
        "routes": [],
        "dependencies": {"internal": set(), "external": set()},
        "metrics": {"lines": 0, "complexity": 0, "functions": 0, "classes": 0}
    })
    
    for file_data in files_data:
        path = Path(file_data['path'])
        
        # Determine module
        if 'app/modules/' in file_data['path']:
            # AI module
            parts = path.parts
            module_idx = parts.index('modules') + 1
            if module_idx < len(parts):
                module_name = parts[module_idx]
                modules[module_name]["name"] = module_name
                modules[module_name]["type"] = "ai_module"
        elif 'app/' in file_data['path']:
            # Core module
            module_name = "core"
            modules[module_name]["name"] = "core"
            modules[module_name]["type"] = "core"
        else:
            # Scripts or other
            module_name = "scripts"
            modules[module_name]["name"] = "scripts"
            modules[module_name]["type"] = "utility"
        
        # Add file to module
        modules[module_name]["files"].append(file_data)
        
        # Add routes
        if file_data.get('routes'):
            modules[module_name]["routes"].extend(file_data['routes'])
        
        # Update metrics
        modules[module_name]["metrics"]["lines"] += file_data['lines']
        modules[module_name]["metrics"]["complexity"] += file_data['complexity']
        modules[module_name]["metrics"]["functions"] += len(file_data['functions'])
        modules[module_name]["metrics"]["classes"] += len(file_data['classes'])
        
        # Extract dependencies
        for imp in file_data['imports']:
            module_path = imp.get('module', '')
            if module_path.startswith('app.'):
                modules[module_name]["dependencies"]["internal"].add(module_path)
            elif module_path and not module_path.startswith('.'):
                modules[module_name]["dependencies"]["external"].add(module_path.split('.')[0])
    
    # Convert sets to lists for JSON serialization
    for module in modules.values():
        module["dependencies"]["internal"] = sorted(list(module["dependencies"]["internal"]))
        module["dependencies"]["external"] = sorted(list(module["dependencies"]["external"]))
    
    # Build dependency graph
    dependency_graph = {}
    for module_name, module_data in modules.items():
        deps = []
        for internal_dep in module_data["dependencies"]["internal"]:
            # Extract module name from path (e.g., app.modules.transcription -> transcription)
            if 'modules.' in internal_dep:
                dep_module = internal_dep.split('modules.')[1].split('.')[0]
                if dep_module != module_name:
                    deps.append(dep_module)
        dependency_graph[module_name] = list(set(deps))
    
    # Collect all routes
    all_routes = []
    for module_data in modules.values():
        all_routes.extend(module_data["routes"])
    
    return {
        "project": {
            "name": "SaaS-IA MVP",
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "root_path": str(root_path)
        },
        "stats": {
            "total_modules": len(modules),
            "total_files": len(files_data),
            "total_lines": total_lines,
            "total_complexity": total_complexity,
            "total_routes": len(all_routes)
        },
        "modules": [dict(module_data, name=name) for name, module_data in modules.items()],
        "api_endpoints": all_routes,
        "dependency_graph": dependency_graph,
        "architecture_rules": {
            "backend_framework": "FastAPI",
            "orm": "SQLModel",
            "database": "PostgreSQL",
            "cache": "Redis",
            "auth": "JWT",
            "async": True
        }
    }


def main():
    """Main function"""
    # Fix Windows encoding issues
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("PROJECT MAP GENERATOR - SaaS-IA MVP")
    print("=" * 60)
    print()
    
    # Determine project root
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    mvp_dir = backend_dir.parent
    
    print(f"Repertoire backend: {backend_dir}")
    print(f"Repertoire MVP: {mvp_dir}")
    print()
    
    # Scan project
    project_map = scan_project(backend_dir)
    
    # Output path
    output_path = mvp_dir / "project-map.json"
    
    # Write JSON
    print()
    print(f"Ecriture du fichier: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(project_map, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print("PROJECT MAP GENERE AVEC SUCCES !")
    print("=" * 60)
    print()
    print(f"Statistiques:")
    print(f"   - Modules: {project_map['stats']['total_modules']}")
    print(f"   - Fichiers: {project_map['stats']['total_files']}")
    print(f"   - Lignes de code: {project_map['stats']['total_lines']}")
    print(f"   - Complexite totale: {project_map['stats']['total_complexity']}")
    print(f"   - Routes API: {project_map['stats']['total_routes']}")
    print()
    print(f"Fichier genere: {output_path}")
    print()


if __name__ == "__main__":
    main()

