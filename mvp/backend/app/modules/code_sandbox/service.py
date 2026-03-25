"""
Code Sandbox service - secure code execution with AI-powered generation and debugging.

Executes user code in an isolated Docker container (preferred) or a restricted
subprocess (fallback). Docker execution provides true sandboxing: no network,
memory/CPU limits, read-only filesystem, non-root user.

CRIT-02 FIX: Docker-based isolation prevents regex-bypass attacks that could
escape the subprocess sandbox.
"""

import asyncio
import json
import os
import platform
import re
import sys
import time
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.code_sandbox import Sandbox, SandboxStatus

# --- Docker auto-detection (optional dependency) ---
try:
    import docker
    HAS_DOCKER = True
except ImportError:
    docker = None  # type: ignore[assignment]
    HAS_DOCKER = False

logger = structlog.get_logger()

# Maximum execution time in seconds
MAX_EXECUTION_TIMEOUT = 30

# Maximum output size in characters
MAX_OUTPUT_SIZE = 100_000

# Docker container image for sandboxed execution
DOCKER_IMAGE = "python:3.13-slim"

# Docker resource limits
DOCKER_MEM_LIMIT = "256m"
DOCKER_CPU_PERIOD = 100_000
DOCKER_CPU_QUOTA = 50_000  # 50% of one CPU

# Blocked modules that user code cannot import
BLOCKED_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "requests", "httpx",
    "ctypes", "multiprocessing", "threading",
    "signal", "resource", "importlib", "builtins",
    "code", "codeop", "compile", "compileall",
    "pickle", "shelve", "marshal",
    "webbrowser", "antigravity",
    "pty", "fcntl", "termios",
    "sqlite3", "asyncio", "aiohttp",
    "__builtin__", "__import__",
})

# Regex to detect dangerous import patterns
IMPORT_PATTERN = re.compile(
    r"""
    (?:^|\n)\s*                      # start of line
    (?:
        import\s+([\w.,\s]+)         # import x, y
        |from\s+([\w.]+)\s+import    # from x import ...
    )
    """,
    re.VERBOSE,
)

# Regex to detect dangerous builtins usage
DANGEROUS_BUILTINS_PATTERN = re.compile(
    r"\b(?:exec|eval|compile|__import__|globals|locals|getattr|setattr|delattr|open)\s*\("
)


def _validate_code(source: str) -> Optional[str]:
    """Validate code for dangerous patterns. Returns error message or None."""
    # Check for blocked imports
    for match in IMPORT_PATTERN.finditer(source):
        imported = match.group(1) or match.group(2)
        if imported:
            modules = [m.strip().split(".")[0] for m in imported.split(",")]
            for mod in modules:
                if mod in BLOCKED_MODULES:
                    return f"Import of '{mod}' is not allowed for security reasons"

    # Check for dangerous builtins
    if DANGEROUS_BUILTINS_PATTERN.search(source):
        return "Usage of exec/eval/compile/open/__import__ is not allowed for security reasons"

    # Check for file operations
    if re.search(r"\bopen\s*\(", source):
        return "File operations are not allowed for security reasons"

    return None


def _build_restricted_code(source: str) -> str:
    """Wrap user code with restricted builtins and a safe execution sandbox."""
    blocked_repr = repr(BLOCKED_MODULES)
    return (
        "import sys as _sys\n"
        "\n"
        "# Remove dangerous builtins\n"
        "_safe_builtins = dict(__builtins__) if isinstance(__builtins__, dict) else dict(vars(__builtins__))\n"
        'for _name in ["exec", "eval", "compile", "__import__", "open", "globals", "locals",\n'
        '              "getattr", "setattr", "delattr", "breakpoint", "exit", "quit"]:\n'
        "    _safe_builtins.pop(_name, None)\n"
        "\n"
        "# Block dangerous modules from being imported\n"
        f"_BLOCKED = {blocked_repr}\n"
        "\n"
        "class _RestrictedImporter:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "    def find_module(self, name, path=None):\n"
        '        top = name.split(".")[0]\n'
        "        if top in _BLOCKED:\n"
        "            return self\n"
        "        return None\n"
        "    def load_module(self, name):\n"
        "        raise ImportError(f\"Import of '{name}' is not allowed for security reasons\")\n"
        "\n"
        "_sys.meta_path.insert(0, _RestrictedImporter())\n"
        "\n"
        "# Limit recursion depth\n"
        "_sys.setrecursionlimit(200)\n"
        "\n"
        "# Run user code\n"
        f"{source}\n"
    )


def _build_subprocess_env() -> dict:
    """Build a restricted environment for subprocess execution."""
    env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "",
        "PYTHONNOUSERSITE": "1",
        "PYTHONHASHSEED": "random",
    }
    # Preserve minimal PATH so Python can be found
    if "PATH" in os.environ:
        env["PATH"] = os.environ["PATH"]
    # On Windows, SystemRoot is required for subprocess to work
    if platform.system() == "Windows" and "SystemRoot" in os.environ:
        env["SystemRoot"] = os.environ["SystemRoot"]
    return env


def _build_preexec_fn():
    """Build a preexec_fn that sets resource limits on Linux/Unix systems."""
    if platform.system() == "Windows":
        return None

    def _set_limits():
        try:
            import resource as res_mod
            # Max memory: 256 MB
            mem_limit = 256 * 1024 * 1024
            res_mod.setrlimit(res_mod.RLIMIT_AS, (mem_limit, mem_limit))
            # Max CPU time: 30 seconds
            res_mod.setrlimit(res_mod.RLIMIT_CPU, (30, 30))
            # No core dumps
            res_mod.setrlimit(res_mod.RLIMIT_CORE, (0, 0))
            # Max file size: 1 MB (prevent disk filling)
            file_limit = 1 * 1024 * 1024
            res_mod.setrlimit(res_mod.RLIMIT_FSIZE, (file_limit, file_limit))
            # Max number of open files: 16
            res_mod.setrlimit(res_mod.RLIMIT_NOFILE, (16, 16))
            # Max number of processes: 0 (prevent fork bombs)
            res_mod.setrlimit(res_mod.RLIMIT_NPROC, (0, 0))
        except (ImportError, ValueError, OSError):
            pass  # resource module not available or limits not supported

    return _set_limits


async def _execute_in_docker(source: str, language: str = "python", timeout: int = MAX_EXECUTION_TIMEOUT) -> dict:
    """Execute code inside an isolated Docker container.

    Provides true sandboxing:
    - No network access (network_disabled=True)
    - Memory capped at 256 MB
    - CPU limited to 50% of one core
    - Read-only filesystem
    - Runs as 'nobody' (non-root)
    - Container removed after execution
    """
    start = time.monotonic()

    if not HAS_DOCKER:
        return {
            "output": None,
            "error": "Docker is not available for sandboxed execution",
            "execution_time_ms": 0.0,
            "status": "error",
        }

    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        logger.error("docker_client_error", error=str(e))
        return {
            "output": None,
            "error": f"Docker client error: {str(e)[:300]}",
            "execution_time_ms": 0.0,
            "status": "error",
        }

    container = None
    try:
        # Pass code via environment variable to avoid shell injection through stdin
        container = client.containers.run(
            image=DOCKER_IMAGE,
            command=["python", "-I", "-c", source],
            environment={
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": "",
                "PYTHONNOUSERSITE": "1",
            },
            network_disabled=True,
            mem_limit=DOCKER_MEM_LIMIT,
            cpu_period=DOCKER_CPU_PERIOD,
            cpu_quota=DOCKER_CPU_QUOTA,
            read_only=True,
            user="nobody",
            stdin_open=False,
            stdout=True,
            stderr=True,
            detach=True,
            # tmpfs mount so Python can write to /tmp if needed (e.g. __pycache__)
            tmpfs={"/tmp": "size=10m,noexec,nosuid"},
            # Security: drop all capabilities, no new privileges
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
        )

        # Wait for container to finish with timeout
        wait_result = container.wait(timeout=timeout)
        exit_code = wait_result.get("StatusCode", -1)

        elapsed = (time.monotonic() - start) * 1000

        # Capture logs (stdout + stderr)
        raw_stdout = container.logs(stdout=True, stderr=False)
        raw_stderr = container.logs(stdout=False, stderr=True)

        output = raw_stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT_SIZE] if raw_stdout else None
        error = raw_stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT_SIZE] if raw_stderr else None

        if exit_code != 0:
            return {
                "output": output if output else None,
                "error": error or f"Container exited with code {exit_code}",
                "execution_time_ms": round(elapsed, 2),
                "status": "error",
            }

        return {
            "output": output if output else None,
            "error": None,
            "execution_time_ms": round(elapsed, 2),
            "status": "success",
        }

    except docker.errors.ContainerError as e:
        elapsed = (time.monotonic() - start) * 1000
        logger.warning("docker_container_error", error=str(e)[:300])
        return {
            "output": None,
            "error": f"Container execution error: {str(e)[:500]}",
            "execution_time_ms": round(elapsed, 2),
            "status": "error",
        }
    except docker.errors.ImageNotFound:
        elapsed = (time.monotonic() - start) * 1000
        logger.error("docker_image_not_found", image=DOCKER_IMAGE)
        return {
            "output": None,
            "error": f"Docker image '{DOCKER_IMAGE}' not found. Pull it with: docker pull {DOCKER_IMAGE}",
            "execution_time_ms": round(elapsed, 2),
            "status": "error",
        }
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        # ConnectionError or ReadTimeout from docker wait() means timeout
        error_name = type(e).__name__
        if "Timeout" in error_name or "ReadTimeout" in error_name:
            logger.warning("docker_execution_timeout", timeout=timeout)
            return {
                "output": None,
                "error": f"Execution timed out after {timeout} seconds",
                "execution_time_ms": round(elapsed, 2),
                "status": "timeout",
            }
        logger.error("docker_execution_error", error=str(e), error_type=error_name)
        return {
            "output": None,
            "error": f"Docker execution error: {str(e)[:500]}",
            "execution_time_ms": round(elapsed, 2),
            "status": "error",
        }
    finally:
        # Always clean up the container
        if container is not None:
            try:
                container.remove(force=True)
            except Exception:
                pass


async def _execute_code_subprocess(source: str, timeout: int = MAX_EXECUTION_TIMEOUT) -> dict:
    """Execute code in a restricted subprocess with timeout.

    This is the FALLBACK method when Docker is not available.
    Enhanced with resource limits (Linux) and isolation flags.
    """
    validation_error = _validate_code(source)
    if validation_error:
        return {
            "output": None,
            "error": validation_error,
            "execution_time_ms": 0.0,
            "status": "error",
        }

    restricted_code = _build_restricted_code(source)
    restricted_env = _build_subprocess_env()
    preexec_fn = _build_preexec_fn()

    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-I", "-c", restricted_code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            # No stdin to prevent interactive input
            stdin=asyncio.subprocess.DEVNULL,
            env=restricted_env,
            preexec_fn=preexec_fn,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            elapsed = (time.monotonic() - start) * 1000
            return {
                "output": None,
                "error": f"Execution timed out after {timeout} seconds",
                "execution_time_ms": round(elapsed, 2),
                "status": "timeout",
            }

        elapsed = (time.monotonic() - start) * 1000
        output = stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT_SIZE] if stdout else None
        error = stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT_SIZE] if stderr else None

        # Determine status
        if proc.returncode != 0:
            return {
                "output": output if output else None,
                "error": error or f"Process exited with code {proc.returncode}",
                "execution_time_ms": round(elapsed, 2),
                "status": "error",
            }

        return {
            "output": output if output else None,
            "error": None,
            "execution_time_ms": round(elapsed, 2),
            "status": "success",
        }

    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        logger.error("code_execution_error", error=str(e))
        return {
            "output": None,
            "error": f"Execution error: {str(e)[:500]}",
            "execution_time_ms": round(elapsed, 2),
            "status": "error",
        }


class CodeSandboxService:
    """Service for secure code sandbox with AI assistance."""

    @staticmethod
    async def create_sandbox(
        user_id: UUID, data: dict, session: AsyncSession,
    ) -> Sandbox:
        """Create a new code sandbox."""
        sandbox = Sandbox(
            user_id=user_id,
            name=data["name"],
            language=data.get("language", "python"),
            description=data.get("description"),
            cells_json="[]",
            status=SandboxStatus.ACTIVE,
        )
        session.add(sandbox)
        await session.commit()
        await session.refresh(sandbox)
        logger.info("sandbox_created", sandbox_id=str(sandbox.id), user_id=str(user_id))
        return sandbox

    @staticmethod
    async def list_sandboxes(user_id: UUID, session: AsyncSession) -> list[Sandbox]:
        """List user's active sandboxes."""
        result = await session.execute(
            select(Sandbox).where(
                Sandbox.user_id == user_id,
                Sandbox.is_deleted == False,
            ).order_by(Sandbox.updated_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_sandbox(
        user_id: UUID, sandbox_id: UUID, session: AsyncSession,
    ) -> Optional[Sandbox]:
        """Get a sandbox by ID."""
        sandbox = await session.get(Sandbox, sandbox_id)
        if not sandbox or sandbox.user_id != user_id or sandbox.is_deleted:
            return None
        return sandbox

    @staticmethod
    async def delete_sandbox(
        user_id: UUID, sandbox_id: UUID, session: AsyncSession,
    ) -> bool:
        """Soft-delete a sandbox."""
        sandbox = await session.get(Sandbox, sandbox_id)
        if not sandbox or sandbox.user_id != user_id or sandbox.is_deleted:
            return False
        sandbox.is_deleted = True
        sandbox.status = SandboxStatus.ARCHIVED
        sandbox.updated_at = datetime.now(UTC)
        session.add(sandbox)
        await session.commit()
        logger.info("sandbox_deleted", sandbox_id=str(sandbox_id))
        return True

    @staticmethod
    async def add_cell(
        user_id: UUID, sandbox_id: UUID, data: dict, session: AsyncSession,
    ) -> Optional[dict]:
        """Add a cell to a sandbox. Returns the new cell dict."""
        sandbox = await session.get(Sandbox, sandbox_id)
        if not sandbox or sandbox.user_id != user_id or sandbox.is_deleted:
            return None

        cells = json.loads(sandbox.cells_json)
        cell = {
            "id": str(uuid4()),
            "cell_type": data.get("cell_type", "code"),
            "source": data.get("source", ""),
            "language": data.get("language", sandbox.language),
            "output": None,
            "error": None,
            "execution_time_ms": None,
            "status": "idle",
        }
        cells.append(cell)
        sandbox.cells_json = json.dumps(cells, ensure_ascii=False)
        sandbox.updated_at = datetime.now(UTC)
        session.add(sandbox)
        await session.commit()
        return cell

    @staticmethod
    async def update_cell(
        user_id: UUID, sandbox_id: UUID, cell_id: str,
        source: str, session: AsyncSession,
    ) -> Optional[dict]:
        """Update cell source code. Returns updated cell."""
        sandbox = await session.get(Sandbox, sandbox_id)
        if not sandbox or sandbox.user_id != user_id or sandbox.is_deleted:
            return None

        cells = json.loads(sandbox.cells_json)
        for cell in cells:
            if cell["id"] == cell_id:
                cell["source"] = source
                cell["status"] = "idle"
                cell["output"] = None
                cell["error"] = None
                sandbox.cells_json = json.dumps(cells, ensure_ascii=False)
                sandbox.updated_at = datetime.now(UTC)
                session.add(sandbox)
                await session.commit()
                return cell

        return None

    @staticmethod
    async def delete_cell(
        user_id: UUID, sandbox_id: UUID, cell_id: str, session: AsyncSession,
    ) -> bool:
        """Remove a cell from a sandbox."""
        sandbox = await session.get(Sandbox, sandbox_id)
        if not sandbox or sandbox.user_id != user_id or sandbox.is_deleted:
            return False

        cells = json.loads(sandbox.cells_json)
        new_cells = [c for c in cells if c["id"] != cell_id]
        if len(new_cells) == len(cells):
            return False  # cell not found

        sandbox.cells_json = json.dumps(new_cells, ensure_ascii=False)
        sandbox.updated_at = datetime.now(UTC)
        session.add(sandbox)
        await session.commit()
        return True

    @staticmethod
    async def execute_cell(
        user_id: UUID, sandbox_id: UUID, cell_id: str, session: AsyncSession,
    ) -> Optional[dict]:
        """Execute a cell in a restricted subprocess. Returns CellResult dict."""
        sandbox = await session.get(Sandbox, sandbox_id)
        if not sandbox or sandbox.user_id != user_id or sandbox.is_deleted:
            return None

        cells = json.loads(sandbox.cells_json)
        target_cell = None
        for cell in cells:
            if cell["id"] == cell_id:
                target_cell = cell
                break

        if not target_cell:
            return None

        if not target_cell.get("source", "").strip():
            return {
                "cell_id": cell_id,
                "output": None,
                "error": "Cell is empty",
                "execution_time_ms": 0.0,
                "status": "error",
            }

        # Mark as running
        target_cell["status"] = "running"
        sandbox.cells_json = json.dumps(cells, ensure_ascii=False)
        session.add(sandbox)
        await session.flush()

        # Execute code: Docker (secure) if available, subprocess (fallback) otherwise
        cell_language = target_cell.get("language", sandbox.language)
        if HAS_DOCKER:
            execution_method = "docker"
            result = await _execute_in_docker(
                target_cell["source"],
                language=cell_language,
            )
            # If Docker fails at the infra level (daemon down, image missing),
            # fall back to subprocess to avoid blocking the user
            if result["status"] == "error" and result["error"] and (
                "Docker client error" in result["error"]
                or "Docker image" in result["error"]
                or "Docker execution error" in result["error"]
            ):
                logger.warning(
                    "docker_fallback_to_subprocess",
                    reason=result["error"][:200],
                )
                execution_method = "subprocess (docker-fallback)"
                result = await _execute_code_subprocess(target_cell["source"])
        else:
            execution_method = "subprocess"
            result = await _execute_code_subprocess(target_cell["source"])

        # Update cell with result
        target_cell["output"] = result["output"]
        target_cell["error"] = result["error"]
        target_cell["execution_time_ms"] = result["execution_time_ms"]
        target_cell["status"] = result["status"]

        sandbox.cells_json = json.dumps(cells, ensure_ascii=False)
        sandbox.updated_at = datetime.now(UTC)
        session.add(sandbox)
        await session.commit()

        logger.info(
            "cell_executed",
            sandbox_id=str(sandbox_id),
            cell_id=cell_id,
            status=result["status"],
            time_ms=result["execution_time_ms"],
            execution_method=execution_method,
        )

        return {
            "cell_id": cell_id,
            "output": result["output"],
            "error": result["error"],
            "execution_time_ms": result["execution_time_ms"],
            "status": result["status"],
        }

    @staticmethod
    async def generate_code(
        user_id: UUID, prompt: str, language: str, context: Optional[str] = None,
    ) -> dict:
        """Use AI to generate code from a natural language prompt."""
        from app.ai_assistant.service import AIAssistantService

        ai_prompt = f"""You are an expert {language} programmer. Generate clean, working code based on the user's request.

Request: {prompt}
Language: {language}
{f"Context: {context}" if context else ""}

Respond with a JSON object:
{{
  "code": "the generated code",
  "explanation": "brief explanation of what the code does"
}}

Important:
- Write clean, production-quality code
- Include comments for complex logic
- Do NOT use any dangerous modules (os, sys, subprocess, etc.)
- Respond ONLY with the JSON object"""

        try:
            result = await AIAssistantService.process_text_with_provider(
                text=ai_prompt,
                task="code_generation",
                provider_name="gemini",
                user_id=user_id,
                module="code_sandbox",
            )

            response = result.get("processed_text", "{}")
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                parsed = json.loads(response[start:end])
                return {
                    "code": parsed.get("code", ""),
                    "explanation": parsed.get("explanation", ""),
                    "language": language,
                }

            return {"code": response, "explanation": "", "language": language}

        except Exception as e:
            logger.error("code_generation_failed", error=str(e))
            return {
                "code": f"# Error generating code: {str(e)[:200]}",
                "explanation": "Code generation failed",
                "language": language,
            }

    @staticmethod
    async def explain_code(user_id: UUID, code: str) -> dict:
        """Use AI to explain code."""
        from app.ai_assistant.service import AIAssistantService

        ai_prompt = f"""You are an expert programmer. Explain the following code clearly and concisely.

```
{code[:10000]}
```

Respond with a JSON object:
{{
  "explanation": "detailed explanation of the code",
  "complexity": "O(n)/O(n^2)/etc. if applicable, otherwise null"
}}

Respond ONLY with the JSON object."""

        try:
            result = await AIAssistantService.process_text_with_provider(
                text=ai_prompt,
                task="code_explanation",
                provider_name="gemini",
                user_id=user_id,
                module="code_sandbox",
            )

            response = result.get("processed_text", "{}")
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                parsed = json.loads(response[start:end])
                return {
                    "explanation": parsed.get("explanation", ""),
                    "complexity": parsed.get("complexity"),
                }

            return {"explanation": response, "complexity": None}

        except Exception as e:
            logger.error("code_explanation_failed", error=str(e))
            return {"explanation": f"Error: {str(e)[:200]}", "complexity": None}

    @staticmethod
    async def debug_code(user_id: UUID, code: str, error: str) -> dict:
        """Use AI to debug code with error context."""
        from app.ai_assistant.service import AIAssistantService

        ai_prompt = f"""You are an expert debugger. Fix the following code that produces an error.

Code:
```
{code[:10000]}
```

Error:
```
{error[:3000]}
```

Respond with a JSON object:
{{
  "fixed_code": "the corrected code",
  "explanation": "what was changed and why",
  "root_cause": "brief description of the root cause"
}}

Respond ONLY with the JSON object."""

        try:
            result = await AIAssistantService.process_text_with_provider(
                text=ai_prompt,
                task="code_debugging",
                provider_name="gemini",
                user_id=user_id,
                module="code_sandbox",
            )

            response = result.get("processed_text", "{}")
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                parsed = json.loads(response[start:end])
                return {
                    "fixed_code": parsed.get("fixed_code", ""),
                    "explanation": parsed.get("explanation", ""),
                    "root_cause": parsed.get("root_cause", ""),
                }

            return {
                "fixed_code": code,
                "explanation": response,
                "root_cause": "Could not determine root cause",
            }

        except Exception as e:
            logger.error("code_debugging_failed", error=str(e))
            return {
                "fixed_code": code,
                "explanation": f"Error: {str(e)[:200]}",
                "root_cause": "Debugging service failed",
            }
