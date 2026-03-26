"""
Repo Analyzer service - Business logic for GitHub repository analysis.

Analyzes repos for: tech stack, code quality, structure, dependencies, security.
Uses git clone when available, falls back to GitHub API / mock mode.
"""

import asyncio
import json
import os
import re
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session_context
from app.models.repo_analyzer import RepoAnalysis, AnalysisStatus

logger = structlog.get_logger()

# Auto-detect git availability
HAS_GIT = shutil.which("git") is not None

# File extension -> language mapping
EXTENSION_LANGUAGE_MAP = {
    ".py": "Python", ".pyx": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
    ".c": "C", ".h": "C",
    ".swift": "Swift",
    ".scala": "Scala",
    ".r": "R", ".R": "R",
    ".dart": "Dart",
    ".lua": "Lua",
    ".ex": "Elixir", ".exs": "Elixir",
    ".hs": "Haskell",
    ".clj": "Clojure",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "CSS", ".sass": "CSS", ".less": "CSS",
    ".sql": "SQL",
    ".yml": "YAML", ".yaml": "YAML",
    ".json": "JSON",
    ".md": "Markdown", ".mdx": "Markdown",
    ".xml": "XML",
    ".toml": "TOML",
    ".proto": "Protobuf",
    ".graphql": "GraphQL", ".gql": "GraphQL",
}

# Key files to identify in any repo
KEY_FILE_PATTERNS = [
    "README.md", "README.rst", "README.txt", "README",
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "composer.json", "mix.exs",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".circleci/config.yml",
    "Makefile", "CMakeLists.txt",
    ".env", ".env.example", ".env.local",
    "LICENSE", "LICENSE.md", "CONTRIBUTING.md",
    ".gitignore", ".editorconfig",
    "tsconfig.json", "tslint.json", ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml",
    ".prettierrc", ".prettierrc.js", ".prettierrc.json",
    "jest.config.js", "jest.config.ts", "vitest.config.ts",
    "pytest.ini", "pyproject.toml", "tox.ini", ".flake8",
    "mypy.ini", ".mypy.ini",
    "requirements.txt", "requirements-dev.txt", "Pipfile",
    "alembic.ini",
    "next.config.js", "next.config.mjs", "next.config.ts",
    "vite.config.ts", "vite.config.js",
    "webpack.config.js",
    "nginx.conf",
    "Procfile", "fly.toml", "vercel.json", "netlify.toml",
]

# Directories to skip during analysis
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".tox", ".mypy_cache",
    ".pytest_cache", "venv", ".venv", "env", ".env", "dist", "build",
    "target", ".next", ".nuxt", "coverage", ".coverage",
    ".idea", ".vscode", "vendor",
}

# Secret patterns to scan for
SECRET_PATTERNS = [
    (r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "API key"),
    (r"(?:secret|password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Password/Secret"),
    (r"(?:aws_access_key_id|aws_secret_access_key)\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{20,}", "AWS credential"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API key"),
    (r"AIza[a-zA-Z0-9_\-]{35}", "Google API key"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private key"),
    (r"(?:AKIA|ASIA)[A-Z0-9]{16}", "AWS access key ID"),
    (r"xox[bporas]-[a-zA-Z0-9-]+", "Slack token"),
]


class RepoAnalyzerService:
    """Service for analyzing GitHub repositories."""

    def __init__(self):
        self.mock_mode = not HAS_GIT
        if self.mock_mode:
            logger.info("repo_analyzer_mock_mode", reason="git not found in PATH")
        else:
            logger.info("repo_analyzer_git_available")

    @staticmethod
    def is_installed() -> bool:
        """Check if git is available on the system."""
        return HAS_GIT

    @staticmethod
    def _extract_repo_name(repo_url: str) -> str:
        """Extract owner/repo or repo name from a URL."""
        url = repo_url.strip().rstrip("/")
        # Handle owner/repo format
        if not url.startswith("http") and "/" in url:
            return url
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            name = parts[-1].removesuffix(".git")
            return f"{parts[-2]}/{name}"
        return parts[-1] if parts else url

    ALLOWED_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}

    @staticmethod
    def _validate_repo_url(url: str) -> None:
        """Validate that a repo URL points to an allowed Git hosting domain.

        Raises ValueError for disallowed or malformed URLs to prevent SSRF.
        """
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ValueError(
                f"Only HTTPS URLs are allowed, got scheme '{parsed.scheme}'"
            )
        hostname = (parsed.hostname or "").lower()
        if hostname not in RepoAnalyzerService.ALLOWED_HOSTS:
            allowed = ", ".join(sorted(RepoAnalyzerService.ALLOWED_HOSTS))
            raise ValueError(
                f"Repository host '{hostname}' is not allowed. "
                f"Allowed hosts: {allowed}"
            )

    @staticmethod
    def _normalize_repo_url(repo_url: str) -> str:
        """Normalize repo URL to a clonable HTTPS URL."""
        url = repo_url.strip().rstrip("/")
        if not url.startswith("http"):
            if not re.match(r"^[\w.\-]+/[\w.\-]+$", url):
                raise ValueError(
                    "Short-form repo URLs must be in 'owner/repo' format "
                    "(only GitHub is supported for short-form)"
                )
            url = f"https://github.com/{url}"
        RepoAnalyzerService._validate_repo_url(url)
        if url.endswith(".git"):
            return url
        return url + ".git"

    @staticmethod
    async def create_analysis(
        user_id: UUID,
        data,
        session: AsyncSession,
    ) -> RepoAnalysis:
        """Create a new analysis job record."""
        repo_name = RepoAnalyzerService._extract_repo_name(data.repo_url)

        analysis = RepoAnalysis(
            user_id=user_id,
            repo_url=data.repo_url,
            repo_name=repo_name,
            analysis_types_json=json.dumps(data.analysis_types),
            depth=data.depth,
            status=AnalysisStatus.PENDING,
        )
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        logger.info(
            "repo_analysis_created",
            analysis_id=str(analysis.id),
            user_id=str(user_id),
            repo_url=data.repo_url,
            depth=data.depth,
        )
        return analysis

    async def run_analysis(self, analysis_id: UUID) -> None:
        """Execute an analysis job in the background."""
        async with get_session_context() as session:
            analysis = await session.get(RepoAnalysis, analysis_id)
            if not analysis:
                logger.error("repo_analysis_not_found", analysis_id=str(analysis_id))
                return

            try:
                analysis.status = AnalysisStatus.RUNNING
                analysis.current_step = "starting"
                analysis.updated_at = datetime.now(UTC)
                await session.commit()

                analysis_types = json.loads(analysis.analysis_types_json)
                run_all = "all" in analysis_types

                logger.info(
                    "repo_analysis_started",
                    analysis_id=str(analysis.id),
                    repo_url=analysis.repo_url,
                    mock_mode=self.mock_mode,
                )

                if self.mock_mode:
                    results = await self._run_mock_analysis(
                        analysis, analysis_types, run_all, session,
                    )
                else:
                    results = await self._run_real_analysis(
                        analysis, analysis_types, run_all, session,
                    )

                analysis.status = AnalysisStatus.COMPLETED
                analysis.progress = 100
                analysis.current_step = "done"
                analysis.results_json = json.dumps(results, ensure_ascii=False, default=str)
                analysis.updated_at = datetime.now(UTC)
                await session.commit()

                logger.info("repo_analysis_completed", analysis_id=str(analysis.id))

            except Exception as e:
                analysis.status = AnalysisStatus.FAILED
                analysis.error = str(e)[:2000]
                analysis.current_step = "failed"
                analysis.updated_at = datetime.now(UTC)
                await session.commit()

                logger.error(
                    "repo_analysis_failed",
                    analysis_id=str(analysis.id),
                    error=str(e),
                )

    async def _run_real_analysis(
        self,
        analysis: RepoAnalysis,
        analysis_types: list[str],
        run_all: bool,
        session: AsyncSession,
    ) -> dict:
        """Clone repo and run actual analysis."""
        tmp_dir = tempfile.mkdtemp(prefix="repo_analyzer_")
        repo_path = Path(tmp_dir) / "repo"
        results = {}

        try:
            # Step 1: Clone the repository
            analysis.current_step = "cloning repository"
            analysis.progress = 5
            analysis.updated_at = datetime.now(UTC)
            session.add(analysis)
            await session.commit()

            clone_url = self._normalize_repo_url(analysis.repo_url)
            proc = await asyncio.create_subprocess_exec(
                "git", "clone", "--depth", "1", clone_url, str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            except asyncio.TimeoutError:
                proc.kill()
                raise RuntimeError("git clone timed out (120s limit)")

            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"git clone failed: {error_msg}")

            logger.info("repo_cloned", repo_url=analysis.repo_url, path=str(repo_path))

            # Step 2: Analyze structure
            if run_all or "structure" in analysis_types:
                analysis.current_step = "analyzing structure"
                analysis.progress = 20
                analysis.updated_at = datetime.now(UTC)
                session.add(analysis)
                await session.commit()

                results["structure"] = self._analyze_structure(repo_path)

            # Step 3: Detect tech stack
            if run_all or "tech_stack" in analysis_types:
                analysis.current_step = "detecting tech stack"
                analysis.progress = 35
                analysis.updated_at = datetime.now(UTC)
                session.add(analysis)
                await session.commit()

                results["tech_stack"] = self._detect_tech_stack(repo_path)

            # Step 4: Analyze quality
            if run_all or "quality" in analysis_types:
                analysis.current_step = "scoring quality"
                analysis.progress = 50
                analysis.updated_at = datetime.now(UTC)
                session.add(analysis)
                await session.commit()

                results["quality"] = self._analyze_quality(repo_path)

            # Step 5: Analyze dependencies
            if run_all or "dependencies" in analysis_types:
                analysis.current_step = "analyzing dependencies"
                analysis.progress = 65
                analysis.updated_at = datetime.now(UTC)
                session.add(analysis)
                await session.commit()

                results["dependencies"] = self._analyze_dependencies(repo_path)

            # Step 6: Security scan
            if run_all or "security" in analysis_types:
                analysis.current_step = "running security scan"
                analysis.progress = 75
                analysis.updated_at = datetime.now(UTC)
                session.add(analysis)
                await session.commit()

                results["security"] = self._security_scan(repo_path)

            # Step 7: Generate documentation (deep mode only, uses AI)
            if (run_all or "documentation" in analysis_types) and analysis.depth == "deep":
                analysis.current_step = "generating documentation"
                analysis.progress = 85
                analysis.updated_at = datetime.now(UTC)
                session.add(analysis)
                await session.commit()

                tech_stack = results.get("tech_stack", {})
                results["documentation"] = await self._generate_documentation(
                    repo_path, tech_stack
                )

            analysis.progress = 95
            analysis.updated_at = datetime.now(UTC)
            session.add(analysis)
            await session.commit()

        finally:
            # Cleanup cloned repo
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        return results

    async def _run_mock_analysis(
        self,
        analysis: RepoAnalysis,
        analysis_types: list[str],
        run_all: bool,
        session: AsyncSession,
    ) -> dict:
        """Generate mock analysis results for development/testing."""
        results = {}
        repo_name = analysis.repo_name

        # Simulate processing steps
        steps = [
            ("analyzing structure", 20),
            ("detecting tech stack", 40),
            ("scoring quality", 60),
            ("analyzing dependencies", 75),
            ("running security scan", 90),
        ]

        for step_name, progress in steps:
            analysis.current_step = f"{step_name} (mock)"
            analysis.progress = progress
            analysis.updated_at = datetime.now(UTC)
            session.add(analysis)
            await session.commit()
            await asyncio.sleep(0.5)

        if run_all or "structure" in analysis_types:
            results["structure"] = {
                "total_files": 142,
                "total_lines": 18500,
                "tree": {
                    "src": {"files": 45, "dirs": ["components", "pages", "utils"]},
                    "tests": {"files": 28},
                    "docs": {"files": 8},
                },
                "key_files": [
                    "README.md", "package.json", "Dockerfile",
                    ".github/workflows/ci.yml", "tsconfig.json",
                ],
            }

        if run_all or "tech_stack" in analysis_types:
            results["tech_stack"] = {
                "languages": {"TypeScript": 62.5, "JavaScript": 15.3, "Python": 12.8, "Shell": 5.2, "YAML": 4.2},
                "frameworks": ["Next.js", "React", "FastAPI"],
                "build_tools": ["npm", "webpack", "Docker"],
                "package_manager": "npm",
                "runtime": "Node.js 20 + Python 3.13",
            }

        if run_all or "quality" in analysis_types:
            results["quality"] = {
                "score": 78.0,
                "grade": "B+",
                "issues": [
                    "Missing CONTRIBUTING.md",
                    "No code coverage configuration found",
                    "Some files exceed 500 lines",
                ],
                "recommendations": [
                    "Add CONTRIBUTING.md for open-source best practices",
                    "Configure code coverage (e.g., istanbul, coverage.py)",
                    "Consider splitting large files into smaller modules",
                    "Add pre-commit hooks for linting",
                ],
            }

        if run_all or "dependencies" in analysis_types:
            results["dependencies"] = {
                "total": 87,
                "direct": 34,
                "dev": 53,
                "outdated": [
                    "react@18.2.0 -> 19.0.0",
                    "eslint@8.50.0 -> 9.0.0",
                ],
                "vulnerabilities": [],
            }

        if run_all or "security" in analysis_types:
            results["security"] = {
                "issues": [],
                "risk_level": "low",
                "secrets_found": 0,
                "env_files_committed": 0,
            }

        if (run_all or "documentation" in analysis_types) and analysis.depth == "deep":
            results["documentation"] = {
                "readme_suggestions": [
                    "Add installation instructions",
                    "Add API documentation section",
                    "Add architecture diagram",
                ],
                "architecture_overview": (
                    f"**{repo_name}** is a full-stack application using Next.js for the frontend "
                    f"and FastAPI for the backend. The project follows a modular architecture "
                    f"with clear separation of concerns. (Mock analysis - install git for real results)"
                ),
                "api_docs_suggestions": [
                    "Document REST API endpoints with OpenAPI",
                    "Add request/response examples",
                ],
            }

        return results

    @staticmethod
    def _analyze_structure(repo_path: Path) -> dict:
        """Walk directory and analyze file structure."""
        total_files = 0
        total_lines = 0
        tree = {}
        key_files_found = []
        extension_counts = defaultdict(int)

        for root, dirs, files in os.walk(repo_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            rel_root = os.path.relpath(root, repo_path)
            if rel_root == ".":
                rel_root = ""

            for filename in files:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, repo_path)
                total_files += 1

                # Count lines
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                    total_lines += line_count
                except Exception:
                    pass

                # Track extensions
                ext = os.path.splitext(filename)[1].lower()
                if ext:
                    extension_counts[ext] += 1

                # Check for key files
                for pattern in KEY_FILE_PATTERNS:
                    if rel_path == pattern or filename == pattern:
                        if rel_path not in key_files_found:
                            key_files_found.append(rel_path)
                        break
                    if pattern.endswith("/") and rel_path.startswith(pattern):
                        if rel_path not in key_files_found:
                            key_files_found.append(rel_path)
                        break

        # Build simplified tree (top-level dirs with file counts)
        for item in os.listdir(repo_path):
            item_path = repo_path / item
            if item in SKIP_DIRS or item.startswith("."):
                continue
            if item_path.is_dir():
                dir_files = sum(
                    len(f) for _, _, f in os.walk(item_path)
                    if all(skip not in _ for skip in SKIP_DIRS)
                )
                tree[item] = {"type": "directory", "files": dir_files}
            else:
                tree[item] = {"type": "file"}

        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "tree": tree,
            "key_files": key_files_found[:30],
            "extension_counts": dict(sorted(extension_counts.items(), key=lambda x: -x[1])[:20]),
        }

    @staticmethod
    def _detect_tech_stack(repo_path: Path) -> dict:
        """Detect tech stack from file extensions and config files."""
        languages = defaultdict(int)
        frameworks = []
        build_tools = []
        package_manager = "unknown"
        runtime = "unknown"

        total_code_lines = 0

        # Count lines per language
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                lang = EXTENSION_LANGUAGE_MAP.get(ext)
                if lang and lang not in ("JSON", "YAML", "TOML", "XML", "Markdown"):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            lines = sum(1 for _ in f)
                        languages[lang] += lines
                        total_code_lines += lines
                    except Exception:
                        pass

        # Convert to percentages
        lang_percentages = {}
        if total_code_lines > 0:
            for lang, lines in sorted(languages.items(), key=lambda x: -x[1]):
                pct = round((lines / total_code_lines) * 100, 1)
                if pct >= 0.5:
                    lang_percentages[lang] = pct

        # Detect from config files
        has_file = lambda name: (repo_path / name).exists()
        read_file = lambda name: (repo_path / name).read_text(encoding="utf-8", errors="ignore") if has_file(name) else ""

        # Python
        if has_file("pyproject.toml") or has_file("requirements.txt") or has_file("setup.py"):
            package_manager = "pip"
            runtime = "Python"
            pyproject = read_file("pyproject.toml")
            requirements = read_file("requirements.txt")
            all_deps = pyproject + requirements

            if "fastapi" in all_deps.lower():
                frameworks.append("FastAPI")
            if "django" in all_deps.lower():
                frameworks.append("Django")
            if "flask" in all_deps.lower():
                frameworks.append("Flask")
            if "sqlalchemy" in all_deps.lower() or "sqlmodel" in all_deps.lower():
                frameworks.append("SQLAlchemy/SQLModel")
            if "celery" in all_deps.lower():
                frameworks.append("Celery")
            if "pytest" in all_deps.lower():
                build_tools.append("pytest")

            if has_file("Pipfile"):
                package_manager = "pipenv"
            elif has_file("poetry.lock"):
                package_manager = "poetry"
            elif has_file("uv.lock"):
                package_manager = "uv"

        # JavaScript/TypeScript
        if has_file("package.json"):
            try:
                pkg = json.loads(read_file("package.json"))
                all_deps_js = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {}),
                }

                if "next" in all_deps_js:
                    frameworks.append("Next.js")
                if "react" in all_deps_js:
                    frameworks.append("React")
                if "vue" in all_deps_js:
                    frameworks.append("Vue.js")
                if "@angular/core" in all_deps_js:
                    frameworks.append("Angular")
                if "express" in all_deps_js:
                    frameworks.append("Express")
                if "nuxt" in all_deps_js:
                    frameworks.append("Nuxt.js")
                if "svelte" in all_deps_js:
                    frameworks.append("Svelte")
                if "tailwindcss" in all_deps_js:
                    frameworks.append("Tailwind CSS")

                # Package manager detection
                if has_file("pnpm-lock.yaml"):
                    package_manager = "pnpm"
                elif has_file("yarn.lock"):
                    package_manager = "yarn"
                elif has_file("bun.lockb"):
                    package_manager = "bun"
                elif has_file("package-lock.json"):
                    package_manager = "npm"

                if runtime == "unknown":
                    runtime = "Node.js"

            except (json.JSONDecodeError, Exception):
                pass

        # Go
        if has_file("go.mod"):
            package_manager = "go modules"
            runtime = "Go"
            go_mod = read_file("go.mod")
            if "github.com/gin-gonic/gin" in go_mod:
                frameworks.append("Gin")
            if "github.com/gofiber/fiber" in go_mod:
                frameworks.append("Fiber")

        # Rust
        if has_file("Cargo.toml"):
            package_manager = "cargo"
            runtime = "Rust"
            cargo = read_file("Cargo.toml")
            if "actix" in cargo:
                frameworks.append("Actix")
            if "rocket" in cargo:
                frameworks.append("Rocket")
            if "tokio" in cargo:
                frameworks.append("Tokio")

        # Java
        if has_file("pom.xml"):
            package_manager = "maven"
            runtime = "Java"
            build_tools.append("Maven")
            pom = read_file("pom.xml")
            if "spring" in pom.lower():
                frameworks.append("Spring")
        elif has_file("build.gradle") or has_file("build.gradle.kts"):
            package_manager = "gradle"
            runtime = "Java"
            build_tools.append("Gradle")

        # Build tools
        if has_file("Dockerfile"):
            build_tools.append("Docker")
        if has_file("docker-compose.yml") or has_file("docker-compose.yaml"):
            build_tools.append("Docker Compose")
        if has_file("Makefile"):
            build_tools.append("Make")
        if has_file(".github/workflows"):
            build_tools.append("GitHub Actions")
        if has_file(".gitlab-ci.yml"):
            build_tools.append("GitLab CI")
        if has_file("Jenkinsfile"):
            build_tools.append("Jenkins")
        if has_file("webpack.config.js"):
            build_tools.append("Webpack")
        if has_file("vite.config.ts") or has_file("vite.config.js"):
            build_tools.append("Vite")
        if has_file("turbo.json"):
            build_tools.append("Turborepo")

        # Deduplicate
        frameworks = list(dict.fromkeys(frameworks))
        build_tools = list(dict.fromkeys(build_tools))

        return {
            "languages": lang_percentages,
            "frameworks": frameworks,
            "build_tools": build_tools,
            "package_manager": package_manager,
            "runtime": runtime,
        }

    @staticmethod
    def _analyze_quality(repo_path: Path) -> dict:
        """Score repo quality based on best practices."""
        score = 0.0
        issues = []
        recommendations = []
        has_file = lambda name: (repo_path / name).exists()
        has_dir = lambda name: (repo_path / name).is_dir()

        # Has tests (20 pts)
        has_tests = (
            has_dir("tests") or has_dir("test") or has_dir("__tests__")
            or has_dir("spec") or has_file("jest.config.js") or has_file("jest.config.ts")
            or has_file("vitest.config.ts") or has_file("pytest.ini")
        )
        if has_tests:
            score += 20
        else:
            issues.append("No test directory or test configuration found")
            recommendations.append("Add tests to improve reliability and maintainability")

        # Has CI (15 pts)
        has_ci = (
            has_dir(".github/workflows") or has_file(".gitlab-ci.yml")
            or has_file("Jenkinsfile") or has_file(".circleci/config.yml")
            or has_file(".travis.yml") or has_file("azure-pipelines.yml")
        )
        if has_ci:
            score += 15
        else:
            issues.append("No CI/CD configuration found")
            recommendations.append("Set up continuous integration (GitHub Actions, GitLab CI, etc.)")

        # Has README (10 pts)
        has_readme = has_file("README.md") or has_file("README.rst") or has_file("README.txt") or has_file("README")
        if has_readme:
            score += 10
            # Check README quality
            readme_path = repo_path / "README.md"
            if not readme_path.exists():
                for name in ["README.rst", "README.txt", "README"]:
                    if (repo_path / name).exists():
                        readme_path = repo_path / name
                        break
            if readme_path.exists():
                readme_content = readme_path.read_text(encoding="utf-8", errors="ignore")
                if len(readme_content) < 200:
                    issues.append("README is very short (< 200 chars)")
                    recommendations.append("Expand README with installation, usage, and contribution sections")
        else:
            issues.append("No README file found")
            recommendations.append("Create a README.md with project description, installation, and usage")

        # Has docs (10 pts)
        has_docs = has_dir("docs") or has_dir("doc") or has_dir("documentation")
        if has_docs:
            score += 10
        else:
            recommendations.append("Consider adding a docs/ directory for detailed documentation")

        # Has linting config (10 pts)
        has_linting = (
            has_file(".eslintrc") or has_file(".eslintrc.js") or has_file(".eslintrc.json")
            or has_file(".eslintrc.yml") or has_file(".flake8") or has_file(".pylintrc")
            or has_file("ruff.toml") or has_file(".ruff.toml")
        )
        # Also check pyproject.toml for ruff/flake8 config
        if not has_linting and has_file("pyproject.toml"):
            pyproject = (repo_path / "pyproject.toml").read_text(encoding="utf-8", errors="ignore")
            if "[tool.ruff]" in pyproject or "[tool.flake8]" in pyproject or "[tool.pylint]" in pyproject:
                has_linting = True

        if has_linting:
            score += 10
        else:
            issues.append("No linting configuration found")
            recommendations.append("Add a linter (ESLint, Ruff, Flake8) for consistent code style")

        # Has type checking (10 pts)
        has_types = (
            has_file("tsconfig.json") or has_file("mypy.ini") or has_file(".mypy.ini")
            or has_file("pyrightconfig.json")
        )
        if not has_types and has_file("pyproject.toml"):
            pyproject = (repo_path / "pyproject.toml").read_text(encoding="utf-8", errors="ignore")
            if "[tool.mypy]" in pyproject or "[tool.pyright]" in pyproject:
                has_types = True

        if has_types:
            score += 10
        else:
            recommendations.append("Add type checking (TypeScript, mypy, pyright) for better code safety")

        # Code/test ratio (15 pts)
        if has_tests:
            test_files = 0
            code_files = 0
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in EXTENSION_LANGUAGE_MAP:
                        rel = os.path.relpath(root, repo_path)
                        if any(t in rel for t in ["test", "tests", "__tests__", "spec"]) or f.startswith("test_") or f.endswith("_test.py"):
                            test_files += 1
                        else:
                            code_files += 1
            if code_files > 0:
                ratio = test_files / code_files
                if ratio >= 0.5:
                    score += 15
                elif ratio >= 0.3:
                    score += 10
                elif ratio >= 0.1:
                    score += 5
                else:
                    issues.append(f"Low test-to-code ratio ({ratio:.1%})")
                    recommendations.append("Increase test coverage to at least 30% of code files")
            else:
                score += 5  # No source code to test

        # Has license (5 pts)
        has_license = has_file("LICENSE") or has_file("LICENSE.md") or has_file("LICENSE.txt") or has_file("LICENCE")
        if has_license:
            score += 5
        else:
            issues.append("No LICENSE file found")
            recommendations.append("Add a LICENSE file (MIT, Apache 2.0, etc.) for clear usage rights")

        # Has .gitignore (5 pts)
        if has_file(".gitignore"):
            score += 5
        else:
            issues.append("No .gitignore file found")
            recommendations.append("Add a .gitignore file to avoid committing build artifacts and secrets")

        # Calculate grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "A-"
        elif score >= 70:
            grade = "B+"
        elif score >= 60:
            grade = "B"
        elif score >= 50:
            grade = "B-"
        elif score >= 40:
            grade = "C"
        elif score >= 30:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": round(score, 1),
            "grade": grade,
            "issues": issues,
            "recommendations": recommendations,
        }

    @staticmethod
    def _analyze_dependencies(repo_path: Path) -> dict:
        """Parse dependency files and count dependencies."""
        direct = 0
        dev = 0
        outdated = []
        vulnerabilities = []

        has_file = lambda name: (repo_path / name).exists()
        read_file = lambda name: (repo_path / name).read_text(encoding="utf-8", errors="ignore") if has_file(name) else ""

        # Python: requirements.txt
        if has_file("requirements.txt"):
            for line in read_file("requirements.txt").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    direct += 1

        # Python: requirements-dev.txt
        if has_file("requirements-dev.txt"):
            for line in read_file("requirements-dev.txt").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    dev += 1

        # Python: pyproject.toml
        if has_file("pyproject.toml"):
            pyproject = read_file("pyproject.toml")
            # Count [project.dependencies]
            in_deps = False
            in_dev_deps = False
            for line in pyproject.splitlines():
                stripped = line.strip()
                if stripped.startswith("["):
                    in_deps = stripped == "[project.dependencies]" or "dependencies" in stripped and "optional" not in stripped.lower() and "dev" not in stripped.lower()
                    in_dev_deps = "dev" in stripped.lower() or "optional" in stripped.lower()
                    continue
                if in_deps and stripped and not stripped.startswith("#") and "=" not in stripped.split('"')[0]:
                    # It's a dependency line like "fastapi>=0.100"
                    if stripped.startswith('"') or stripped.startswith("'"):
                        direct += 1
                elif in_dev_deps and stripped and stripped.startswith('"'):
                    dev += 1

        # JavaScript: package.json
        if has_file("package.json"):
            try:
                pkg = json.loads(read_file("package.json"))
                direct += len(pkg.get("dependencies", {}))
                dev += len(pkg.get("devDependencies", {}))
            except (json.JSONDecodeError, Exception):
                pass

        # Go: go.mod
        if has_file("go.mod"):
            for line in read_file("go.mod").splitlines():
                if line.strip().startswith("require") or (line.strip() and not line.strip().startswith("//") and not line.strip().startswith("module") and not line.strip().startswith("go ")):
                    if "\t" in line or "  " in line:
                        direct += 1

        # Rust: Cargo.toml
        if has_file("Cargo.toml"):
            cargo = read_file("Cargo.toml")
            in_deps = False
            in_dev = False
            for line in cargo.splitlines():
                stripped = line.strip()
                if stripped == "[dependencies]":
                    in_deps = True
                    in_dev = False
                elif stripped == "[dev-dependencies]":
                    in_dev = True
                    in_deps = False
                elif stripped.startswith("["):
                    in_deps = False
                    in_dev = False
                elif in_deps and "=" in stripped and not stripped.startswith("#"):
                    direct += 1
                elif in_dev and "=" in stripped and not stripped.startswith("#"):
                    dev += 1

        total = direct + dev
        return {
            "total": total,
            "direct": direct,
            "dev": dev,
            "outdated": outdated,
            "vulnerabilities": vulnerabilities,
        }

    @staticmethod
    def _security_scan(repo_path: Path) -> dict:
        """Scan for committed secrets and security issues."""
        issues = []
        secrets_found = 0
        env_files = 0

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for filename in files:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, repo_path)

                # Check for committed .env files
                if filename in (".env", ".env.local", ".env.production", ".env.staging"):
                    env_files += 1
                    issues.append({
                        "type": "env_file_committed",
                        "file": rel_path,
                        "severity": "high",
                        "message": f"Environment file '{filename}' is committed to the repository",
                    })

                # Scan for secrets in source files
                ext = os.path.splitext(filename)[1].lower()
                scannable = ext in (
                    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs",
                    ".java", ".rb", ".php", ".env", ".yml", ".yaml",
                    ".json", ".toml", ".cfg", ".ini", ".conf",
                )
                if not scannable:
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(50000)  # Limit to 50KB per file

                    for pattern, secret_type in SECRET_PATTERNS:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            secrets_found += len(matches)
                            issues.append({
                                "type": "hardcoded_secret",
                                "file": rel_path,
                                "severity": "critical",
                                "message": f"Possible {secret_type} found in {rel_path}",
                                "count": len(matches),
                            })
                except Exception:
                    pass

        # Determine risk level
        if secrets_found > 0:
            risk_level = "critical"
        elif env_files > 0:
            risk_level = "high"
        elif issues:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "issues": issues[:50],  # Cap at 50 issues
            "risk_level": risk_level,
            "secrets_found": secrets_found,
            "env_files_committed": env_files,
        }

    @staticmethod
    async def _generate_documentation(repo_path: Path, tech_stack: dict) -> dict:
        """Use AI to generate documentation suggestions."""
        try:
            from app.ai_assistant.service import AIAssistantService

            # Read README if it exists
            readme_content = ""
            for name in ["README.md", "README.rst", "README.txt", "README"]:
                readme_path = repo_path / name
                if readme_path.exists():
                    readme_content = readme_path.read_text(encoding="utf-8", errors="ignore")[:5000]
                    break

            frameworks = ", ".join(tech_stack.get("frameworks", [])) or "Unknown"
            languages = ", ".join(tech_stack.get("languages", {}).keys()) or "Unknown"

            prompt = (
                f"Analyze this repository and provide documentation suggestions.\n\n"
                f"Languages: {languages}\n"
                f"Frameworks: {frameworks}\n"
                f"Package Manager: {tech_stack.get('package_manager', 'unknown')}\n\n"
                f"Current README (truncated):\n{readme_content[:3000]}\n\n"
                f"Provide a JSON response with:\n"
                f"1. readme_suggestions: list of improvements for the README\n"
                f"2. architecture_overview: a brief description of the project architecture\n"
                f"3. api_docs_suggestions: list of API documentation improvements\n\n"
                f"Respond ONLY with valid JSON."
            )

            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="documentation_analysis",
                provider_name="gemini",
            )

            response_text = result.get("processed_text", "{}")

            # Try to parse JSON from response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(response_text[start:end])
                return {
                    "readme_suggestions": parsed.get("readme_suggestions", []),
                    "architecture_overview": parsed.get("architecture_overview", ""),
                    "api_docs_suggestions": parsed.get("api_docs_suggestions", []),
                }

        except Exception as e:
            logger.warning("documentation_generation_failed", error=str(e))

        return {
            "readme_suggestions": ["Could not generate AI suggestions. Check AI provider configuration."],
            "architecture_overview": "",
            "api_docs_suggestions": [],
        }

    @staticmethod
    async def list_analyses(
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[RepoAnalysis], int]:
        """List analyses for a user with pagination."""
        count_result = await session.execute(
            select(func.count()).select_from(RepoAnalysis).where(
                RepoAnalysis.user_id == user_id
            )
        )
        total = count_result.scalar_one()

        result = await session.execute(
            select(RepoAnalysis)
            .where(RepoAnalysis.user_id == user_id)
            .order_by(RepoAnalysis.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        analyses = list(result.scalars().all())

        return analyses, total

    @staticmethod
    async def get_analysis(
        user_id: UUID,
        analysis_id: UUID,
        session: AsyncSession,
    ) -> Optional[RepoAnalysis]:
        """Get a single analysis by ID, verifying ownership."""
        analysis = await session.get(RepoAnalysis, analysis_id)
        if analysis and analysis.user_id != user_id:
            return None
        return analysis

    @staticmethod
    async def delete_analysis(
        user_id: UUID,
        analysis_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete an analysis."""
        analysis = await session.get(RepoAnalysis, analysis_id)
        if not analysis or analysis.user_id != user_id:
            return False

        session.delete(analysis)
        await session.commit()

        logger.info("repo_analysis_deleted", analysis_id=str(analysis_id))
        return True

    async def compare_repos(
        self,
        user_id: UUID,
        repo_urls: list[str],
        analysis_types: list[str],
        session: AsyncSession,
    ) -> dict:
        """Compare 2-5 repositories side by side."""
        from app.modules.repo_analyzer.schemas import AnalysisCreate

        results = []
        for url in repo_urls[:5]:
            data = AnalysisCreate(
                repo_url=url,
                analysis_types=analysis_types,
                depth="standard",
            )
            analysis = await self.create_analysis(user_id, data, session)
            await self.run_analysis(analysis.id)

            # Reload to get results
            async with get_session_context() as reload_session:
                refreshed = await reload_session.get(RepoAnalysis, analysis.id)
                if refreshed and refreshed.results_json:
                    repo_result = json.loads(refreshed.results_json)
                    repo_result["repo_url"] = url
                    repo_result["repo_name"] = self._extract_repo_name(url)
                    repo_result["status"] = refreshed.status.value if hasattr(refreshed.status, "value") else refreshed.status
                    results.append(repo_result)
                else:
                    results.append({
                        "repo_url": url,
                        "repo_name": self._extract_repo_name(url),
                        "status": "failed",
                        "error": refreshed.error if refreshed else "Analysis not found",
                    })

        # Build comparison summary
        summary = {
            "total_repos": len(results),
            "successful": sum(1 for r in results if r.get("status") == "completed"),
        }

        # Compare quality scores if available
        quality_scores = []
        for r in results:
            q = r.get("quality", {})
            if q and "score" in q:
                quality_scores.append({
                    "repo": r.get("repo_name", ""),
                    "score": q["score"],
                    "grade": q.get("grade", ""),
                })
        if quality_scores:
            quality_scores.sort(key=lambda x: -x["score"])
            summary["quality_ranking"] = quality_scores

        return {
            "repos": results,
            "summary": summary,
        }

    @staticmethod
    def analysis_to_read(analysis: RepoAnalysis) -> dict:
        """Convert a RepoAnalysis model to the AnalysisRead response format."""
        results = None
        if analysis.results_json:
            try:
                results = json.loads(analysis.results_json)
            except (json.JSONDecodeError, Exception):
                results = None

        analysis_types = ["all"]
        try:
            analysis_types = json.loads(analysis.analysis_types_json)
        except (json.JSONDecodeError, Exception):
            pass

        return {
            "id": analysis.id,
            "user_id": analysis.user_id,
            "repo_url": analysis.repo_url,
            "repo_name": analysis.repo_name,
            "status": analysis.status.value if hasattr(analysis.status, "value") else analysis.status,
            "analysis_types": analysis_types,
            "depth": analysis.depth,
            "results": results,
            "error": analysis.error,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
        }
