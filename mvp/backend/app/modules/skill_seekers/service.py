"""
Skill Seekers service - Business logic for GitHub repo scraping and packaging.
"""

import asyncio
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session_context
from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus

logger = structlog.get_logger()

# Repo name security whitelist: owner/repo with alphanumerics, hyphens, underscores, dots
REPO_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+$")
SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")

# Auto-detect CLI availability
HAS_SKILL_SEEKERS = shutil.which("skill-seekers") is not None

# Set of job IDs that have been cancelled — checked between steps in run_job
_cancelled_job_ids: set[UUID] = set()

# Persistent output directory (survives restarts, isolated per user/job)
SKILL_SEEKERS_DATA_DIR = Path(
    os.environ.get("SKILL_SEEKERS_DATA_DIR", "")
) if os.environ.get("SKILL_SEEKERS_DATA_DIR") else Path(tempfile.gettempdir()) / "skill_seekers_data"


class SkillSeekersService:
    """Service for managing Skill Seekers scrape jobs."""

    def __init__(self):
        self.mock_mode = not HAS_SKILL_SEEKERS
        if self.mock_mode:
            logger.info("skill_seekers_mock_mode", reason="CLI not found in PATH")
        else:
            logger.info("skill_seekers_cli_available")

    @staticmethod
    def is_installed() -> bool:
        """Check if skill-seekers CLI is available on the system."""
        return HAS_SKILL_SEEKERS

    @staticmethod
    async def get_cli_version() -> Optional[str]:
        """Return the installed skill-seekers CLI version, or None."""
        if not HAS_SKILL_SEEKERS:
            return None
        try:
            proc = await asyncio.create_subprocess_exec(
                "skill-seekers", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            return stdout.decode("utf-8", errors="replace").strip() if proc.returncode == 0 else None
        except Exception:
            return None

    @staticmethod
    def _validate_repo(repo: str) -> bool:
        """Validate repo name matches owner/repo pattern."""
        return bool(REPO_NAME_PATTERN.match(repo))

    @staticmethod
    def _repo_slug(repo: str) -> str:
        """Convert owner/repo to a filesystem-safe slug."""
        return repo.replace("/", "_").replace(".", "-")

    @staticmethod
    def _get_job_dir(user_id: UUID, job_id: UUID) -> Path:
        """Return persistent output directory for a job, creating it if needed."""
        job_dir = SKILL_SEEKERS_DATA_DIR / str(user_id) / str(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    @staticmethod
    async def recover_orphaned_jobs() -> int:
        """Reset jobs stuck in RUNNING status to FAILED (e.g. after server restart)."""
        async with get_session_context() as session:
            result = await session.execute(
                select(ScrapeJob).where(ScrapeJob.status == ScrapeJobStatus.RUNNING)
            )
            orphaned = list(result.scalars().all())
            for job in orphaned:
                job.status = ScrapeJobStatus.FAILED
                job.error = "Job interrupted by server restart"
                job.current_step = "failed (orphaned)"
                job.updated_at = datetime.now(UTC)
                session.add(job)
            if orphaned:
                await session.commit()
                logger.warning("skill_seekers_orphaned_jobs_recovered", count=len(orphaned))
            return len(orphaned)

    @staticmethod
    async def cleanup_old_jobs(max_age_hours: int = 24) -> int:
        """Delete completed/failed jobs older than max_age_hours and their files."""
        from datetime import timedelta
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        async with get_session_context() as session:
            result = await session.execute(
                select(ScrapeJob).where(
                    ScrapeJob.status.in_([ScrapeJobStatus.COMPLETED, ScrapeJobStatus.FAILED]),
                    ScrapeJob.updated_at < cutoff,
                )
            )
            old_jobs = list(result.scalars().all())
            for job in old_jobs:
                # Clean up files
                if job.output_files_json:
                    try:
                        files = json.loads(job.output_files_json)
                        if files:
                            parent_dir = os.path.dirname(files[0])
                            if parent_dir and os.path.isdir(parent_dir):
                                shutil.rmtree(parent_dir, ignore_errors=True)
                    except Exception:
                        pass
                await session.delete(job)
            if old_jobs:
                await session.commit()
                logger.info("skill_seekers_old_jobs_cleaned", count=len(old_jobs), max_age_hours=max_age_hours)
            return len(old_jobs)

    @staticmethod
    async def create_job(
        user_id: UUID,
        repos: list[str],
        targets: list[str],
        enhance: bool,
        session: AsyncSession,
    ) -> ScrapeJob:
        """Create a new scrape job record."""
        # Validate all repo names
        for repo in repos:
            if not SkillSeekersService._validate_repo(repo):
                raise ValueError(f"Invalid repo name: {repo!r}. Must match owner/repo pattern.")

        job = ScrapeJob(
            user_id=user_id,
            repos_json=json.dumps(repos),
            targets_json=json.dumps(targets),
            enhance=enhance,
            status=ScrapeJobStatus.PENDING,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        logger.info(
            "scrape_job_created",
            job_id=str(job.id),
            user_id=str(user_id),
            repos=repos,
            targets=targets,
            enhance=enhance,
            mock_mode=not HAS_SKILL_SEEKERS,
        )
        return job

    async def run_job(self, job_id: UUID) -> None:
        """
        Execute a scrape job in the background.

        Uses skill-seekers CLI when available, otherwise runs mock mode.
        """
        async with get_session_context() as session:
            job = await session.get(ScrapeJob, job_id)
            if not job:
                logger.error("scrape_job_not_found", job_id=str(job_id))
                return

            try:
                job.status = ScrapeJobStatus.RUNNING
                job.current_step = "starting"
                job.updated_at = datetime.now(UTC)
                await session.commit()

                # Check cancellation between steps
                if self._check_cancelled(job_id):
                    logger.info("scrape_job_cancelled_before_start", job_id=str(job_id))
                    return

                repos = json.loads(job.repos_json)
                targets = json.loads(job.targets_json)

                logger.info(
                    "scrape_job_started",
                    job_id=str(job.id),
                    repos=repos,
                    mock_mode=self.mock_mode,
                )

                if self.mock_mode:
                    output_files = await self._run_mock(job, repos, targets, session)
                else:
                    output_files = await self._run_cli(job, repos, targets, session)

                job.status = ScrapeJobStatus.COMPLETED
                job.progress = 100
                job.current_step = "done"
                job.output_files_json = json.dumps(output_files)
                job.updated_at = datetime.now(UTC)
                await session.commit()

                # Auto-index completed scrape results into Knowledge Base (separate session)
                try:
                    from app.modules.knowledge.service import KnowledgeService
                    async with get_session_context() as index_session:
                        for filepath in output_files:
                            if os.path.isfile(filepath):
                                with open(filepath, "r", encoding="utf-8") as f:
                                    content = f.read()
                                if content and len(content.strip()) > 50:
                                    kb_filename = f"skill_seekers_{os.path.basename(filepath)}"
                                    await KnowledgeService.index_text_content(
                                        user_id=job.user_id,
                                        filename=kb_filename,
                                        content=content,
                                        content_type="text/markdown",
                                        session=index_session,
                                    )
                                    logger.info("auto_index_scrape_result", file=kb_filename)
                except Exception as e:
                    logger.warning("auto_index_scrape_failed", error=str(e))

                logger.info(
                    "scrape_job_completed",
                    job_id=str(job.id),
                    output_files=output_files,
                )

            except Exception as e:
                job.status = ScrapeJobStatus.FAILED
                job.error = str(e)[:2000]
                job.current_step = "failed"
                job.updated_at = datetime.now(UTC)
                await session.commit()

                logger.error(
                    "scrape_job_failed",
                    job_id=str(job.id),
                    error=str(e),
                )

    async def _run_cli(
        self,
        job: ScrapeJob,
        repos: list[str],
        targets: list[str],
        session: AsyncSession,
    ) -> list[str]:
        """Run the actual skill-seekers CLI commands."""
        output_dir = str(self._get_job_dir(job.user_id, job.id))
        output_files: list[str] = []
        total_steps = len(repos) * (len(targets) + (1 if job.enhance else 0)) + len(repos)
        step = 0

        try:
            for repo in repos:
                slug = self._repo_slug(repo)
                repo_dir = os.path.join(output_dir, slug)

                # Step 1: Create (scrape repo)
                job.current_step = f"scraping {repo}"
                step += 1
                job.progress = int((step / total_steps) * 100)
                job.updated_at = datetime.now(UTC)
                session.add(job)
                await session.commit()

                if self._check_cancelled(job.id):
                    raise RuntimeError("Job cancelled by user")

                proc = await asyncio.create_subprocess_exec(
                    "skill-seekers", "create", repo,
                    "--output", repo_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.DEVNULL,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
                except asyncio.TimeoutError:
                    proc.kill()
                    raise RuntimeError(f"skill-seekers create timed out for {repo} (300s limit)")

                if proc.returncode != 0:
                    error_msg = stderr.decode("utf-8", errors="replace")[:500]
                    raise RuntimeError(f"skill-seekers create failed for {repo}: {error_msg}")

                logger.info("skill_seekers_create_done", repo=repo, dir=repo_dir)

                # Step 2 (optional): Enhance
                if job.enhance:
                    job.current_step = f"enhancing {repo}"
                    step += 1
                    job.progress = int((step / total_steps) * 100)
                    job.updated_at = datetime.now(UTC)
                    session.add(job)
                    await session.commit()

                    proc = await asyncio.create_subprocess_exec(
                        "skill-seekers", "enhance", repo_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        stdin=asyncio.subprocess.DEVNULL,
                    )
                    try:
                        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
                    except asyncio.TimeoutError:
                        proc.kill()
                        logger.warning("skill_seekers_enhance_timeout", repo=repo)
                        stdout, stderr = b"", b"timeout"
                    if proc.returncode != 0:
                        logger.warning(
                            "skill_seekers_enhance_failed",
                            repo=repo,
                            error=stderr.decode("utf-8", errors="replace")[:500],
                        )

                # Step 3: Package for each target
                for target in targets:
                    job.current_step = f"packaging {repo} for {target}"
                    step += 1
                    job.progress = int((step / total_steps) * 100)
                    job.updated_at = datetime.now(UTC)
                    session.add(job)
                    await session.commit()

                    if self._check_cancelled(job.id):
                        raise RuntimeError("Job cancelled by user")

                    out_filename = f"{slug}_{target}.md"
                    out_path = os.path.join(output_dir, out_filename)

                    proc = await asyncio.create_subprocess_exec(
                        "skill-seekers", "package", repo_dir,
                        "--target", target,
                        "--output", out_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        stdin=asyncio.subprocess.DEVNULL,
                    )
                    try:
                        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
                    except asyncio.TimeoutError:
                        proc.kill()
                        raise RuntimeError(f"skill-seekers package timed out for {repo}/{target} (300s limit)")

                    if proc.returncode != 0:
                        error_msg = stderr.decode("utf-8", errors="replace")[:500]
                        raise RuntimeError(f"skill-seekers package failed for {repo}/{target}: {error_msg}")

                    output_files.append(out_path)
                    logger.info("skill_seekers_package_done", repo=repo, target=target, file=out_path)

        except Exception:
            # Cleanup on failure
            try:
                shutil.rmtree(output_dir, ignore_errors=True)
            except Exception:
                pass
            raise

        return output_files

    async def _run_mock(
        self,
        job: ScrapeJob,
        repos: list[str],
        targets: list[str],
        session: AsyncSession,
    ) -> list[str]:
        """Simulate CLI execution for development/testing."""
        output_dir = str(self._get_job_dir(job.user_id, job.id))
        output_files: list[str] = []
        total_steps = len(repos) * len(targets)
        step = 0

        for repo in repos:
            slug = self._repo_slug(repo)

            # Simulate scraping
            job.current_step = f"scraping {repo} (mock)"
            job.progress = int(((step + 0.5) / total_steps) * 80)
            job.updated_at = datetime.now(UTC)
            session.add(job)
            await session.commit()
            await asyncio.sleep(1.5)

            # Simulate enhance
            if job.enhance:
                job.current_step = f"enhancing {repo} (mock)"
                job.updated_at = datetime.now(UTC)
                session.add(job)
                await session.commit()
                await asyncio.sleep(1.0)

            for target in targets:
                job.current_step = f"packaging {repo} for {target} (mock)"
                step += 1
                job.progress = int((step / total_steps) * 90)
                job.updated_at = datetime.now(UTC)
                session.add(job)
                await session.commit()
                await asyncio.sleep(0.5)

                if self._check_cancelled(job.id):
                    raise RuntimeError("Job cancelled by user")

                out_filename = f"{slug}_{target}.md"
                out_path = os.path.join(output_dir, out_filename)

                mock_content = (
                    f"# {repo} - Packaged for {target}\n\n"
                    f"**Generated by Skill Seekers (MOCK MODE)**\n\n"
                    f"This is a simulated output. Install `skill-seekers` CLI for real results.\n\n"
                    f"```bash\npip install skill-seekers\n```\n\n"
                    f"## Repository Structure\n\n"
                    f"- `src/` - Source code\n"
                    f"- `tests/` - Test suite\n"
                    f"- `README.md` - Documentation\n"
                    f"- `pyproject.toml` - Project config\n\n"
                    f"## Key Files\n\n"
                    f"Mock data for {repo}. Real scraping requires the CLI.\n\n"
                    f"---\n"
                    f"Generated: {datetime.now(UTC).isoformat()}\n"
                )

                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(mock_content)

                output_files.append(out_path)

        return output_files

    @staticmethod
    async def get_jobs(
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[ScrapeJobStatus] = None,
    ) -> tuple[list[ScrapeJob], int]:
        """List scrape jobs for a user with pagination and optional status filter."""
        conditions = [ScrapeJob.user_id == user_id]
        if status_filter is not None:
            conditions.append(ScrapeJob.status == status_filter)

        count_result = await session.execute(
            select(func.count()).select_from(ScrapeJob).where(*conditions)
        )
        total = count_result.scalar_one()

        result = await session.execute(
            select(ScrapeJob)
            .where(*conditions)
            .order_by(ScrapeJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        jobs = list(result.scalars().all())

        return jobs, total

    @staticmethod
    def generate_download_token(job_id: UUID, filename: str, expires_seconds: int = 300) -> str:
        """Generate a HMAC-signed token for authenticated file downloads."""
        import hmac
        import hashlib
        import time
        from app.config import settings
        expiry = int(time.time()) + expires_seconds
        payload = f"{job_id}:{filename}:{expiry}"
        sig = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        return f"{expiry}.{sig}"

    @staticmethod
    def verify_download_token(job_id: UUID, filename: str, token: str) -> bool:
        """Verify a HMAC-signed download token."""
        import hmac
        import hashlib
        import time
        from app.config import settings
        try:
            expiry_str, sig = token.split(".", 1)
            expiry = int(expiry_str)
            if time.time() > expiry:
                return False
            payload = f"{job_id}:{filename}:{expiry}"
            expected = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
            return hmac.compare_digest(sig, expected)
        except Exception:
            return False

    @staticmethod
    async def get_job(
        job_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[ScrapeJob]:
        """Get a single scrape job by ID, verifying ownership."""
        job = await session.get(ScrapeJob, job_id)
        if job and job.user_id != user_id:
            return None
        return job

    @staticmethod
    async def delete_job(
        job_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete a scrape job and clean up output files."""
        job = await session.get(ScrapeJob, job_id)
        if not job or job.user_id != user_id:
            return False

        # Clean up output files
        if job.output_files_json:
            try:
                files = json.loads(job.output_files_json)
                if files:
                    # All files are in the same temp directory
                    parent_dir = os.path.dirname(files[0])
                    if parent_dir and os.path.isdir(parent_dir):
                        shutil.rmtree(parent_dir, ignore_errors=True)
            except Exception as e:
                logger.warning("scrape_job_cleanup_failed", job_id=str(job_id), error=str(e))

        await session.delete(job)
        await session.commit()

        logger.info("scrape_job_deleted", job_id=str(job_id))
        return True

    @staticmethod
    def get_output_file(job: ScrapeJob, filename: str) -> Optional[str]:
        """Return the full path for a job output file if it exists."""
        if not job.output_files_json:
            return None
        if not SAFE_FILENAME_PATTERN.match(filename):
            return None

        files = json.loads(job.output_files_json)
        for filepath in files:
            if os.path.basename(filepath) == filename and os.path.isfile(filepath):
                return filepath

        return None

    @staticmethod
    async def get_user_stats(user_id: UUID, session: AsyncSession) -> dict:
        """Get scrape job statistics for a user."""
        status_result = await session.execute(
            select(
                ScrapeJob.status,
                func.count().label("cnt"),
            )
            .where(ScrapeJob.user_id == user_id)
            .group_by(ScrapeJob.status)
        )
        status_counts: dict[str, int] = {}
        for row in status_result.all():
            status_counts[row.status] = row.cnt

        completed = status_counts.get(ScrapeJobStatus.COMPLETED, 0)
        failed = status_counts.get(ScrapeJobStatus.FAILED, 0)
        pending = status_counts.get(ScrapeJobStatus.PENDING, 0)
        running = status_counts.get(ScrapeJobStatus.RUNNING, 0)
        total = completed + failed + pending + running

        # Count total repos scraped across completed jobs
        repos_result = await session.execute(
            select(ScrapeJob.repos_json)
            .where(ScrapeJob.user_id == user_id)
            .where(ScrapeJob.status == ScrapeJobStatus.COMPLETED)
        )
        total_repos = 0
        for row in repos_result.all():
            try:
                total_repos += len(json.loads(row[0]))
            except Exception:
                pass

        # Recent jobs (last 5)
        recent_result = await session.execute(
            select(ScrapeJob)
            .where(ScrapeJob.user_id == user_id)
            .order_by(ScrapeJob.created_at.desc())
            .limit(5)
        )
        recent_jobs = [
            {
                "id": str(job.id),
                "repos": json.loads(job.repos_json) if job.repos_json else [],
                "status": job.status.value if hasattr(job.status, "value") else job.status,
                "created_at": job.created_at.isoformat(),
            }
            for job in recent_result.scalars().all()
        ]

        return {
            "total_jobs": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "total_repos_scraped": total_repos,
            "recent_jobs": recent_jobs,
        }

    @staticmethod
    async def retry_job(
        job_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[ScrapeJob]:
        """Clone a failed job and reset it to pending for re-execution."""
        original = await session.get(ScrapeJob, job_id)
        if not original or original.user_id != user_id:
            return None
        if original.status != ScrapeJobStatus.FAILED:
            return None

        new_job = ScrapeJob(
            user_id=user_id,
            repos_json=original.repos_json,
            targets_json=original.targets_json,
            enhance=original.enhance,
            status=ScrapeJobStatus.PENDING,
        )
        session.add(new_job)
        await session.commit()
        await session.refresh(new_job)

        logger.info(
            "scrape_job_retried",
            original_id=str(job_id),
            new_id=str(new_job.id),
        )
        return new_job

    @staticmethod
    async def cancel_job(
        job_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Cancel a running or pending job."""
        job = await session.get(ScrapeJob, job_id)
        if not job or job.user_id != user_id:
            return False
        if job.status not in (ScrapeJobStatus.PENDING, ScrapeJobStatus.RUNNING):
            return False

        # Signal the background task to stop
        _cancelled_job_ids.add(job_id)

        job.status = ScrapeJobStatus.FAILED
        job.error = "Cancelled by user"
        job.current_step = "cancelled"
        job.updated_at = datetime.now(UTC)
        session.add(job)
        await session.commit()

        logger.info("scrape_job_cancelled", job_id=str(job_id))
        return True

    @staticmethod
    def _check_cancelled(job_id: UUID) -> bool:
        """Check if a job has been cancelled. If so, remove from set and return True."""
        if job_id in _cancelled_job_ids:
            _cancelled_job_ids.discard(job_id)
            return True
        return False

    @staticmethod
    def get_file_preview(job: ScrapeJob, filename: str, max_chars: int = 5000) -> Optional[str]:
        """Return the first max_chars+1 characters of an output file for truncation detection."""
        if not job.output_files_json:
            return None
        if not SAFE_FILENAME_PATTERN.match(filename):
            return None

        files = json.loads(job.output_files_json)
        for filepath in files:
            if os.path.basename(filepath) == filename and os.path.isfile(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read(max_chars + 1)
        return None

    @staticmethod
    def job_to_read(job: ScrapeJob) -> dict:
        """Convert a ScrapeJob model to the ScrapeJobRead response format."""
        return {
            "id": job.id,
            "user_id": job.user_id,
            "repos": json.loads(job.repos_json) if job.repos_json else [],
            "targets": json.loads(job.targets_json) if job.targets_json else [],
            "enhance": job.enhance,
            "status": job.status.value if hasattr(job.status, "value") else job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "output_files": [
                os.path.basename(f)
                for f in json.loads(job.output_files_json)
            ] if job.output_files_json else [],
            "error": job.error,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
