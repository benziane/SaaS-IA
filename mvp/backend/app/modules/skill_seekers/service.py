"""
Skill Seekers service - Business logic for GitHub repo scraping and packaging.
"""

import asyncio
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
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

# Auto-detect CLI availability
HAS_SKILL_SEEKERS = shutil.which("skill-seekers") is not None


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
    def _validate_repo(repo: str) -> bool:
        """Validate repo name matches owner/repo pattern."""
        return bool(REPO_NAME_PATTERN.match(repo))

    @staticmethod
    def _repo_slug(repo: str) -> str:
        """Convert owner/repo to a filesystem-safe slug."""
        return repo.replace("/", "_").replace(".", "-")

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
                job.updated_at = datetime.utcnow()
                await session.commit()

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
                job.updated_at = datetime.utcnow()
                await session.commit()

                logger.info(
                    "scrape_job_completed",
                    job_id=str(job.id),
                    output_files=output_files,
                )

            except Exception as e:
                job.status = ScrapeJobStatus.FAILED
                job.error = str(e)[:2000]
                job.current_step = "failed"
                job.updated_at = datetime.utcnow()
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
        output_dir = tempfile.mkdtemp(prefix="skill_seekers_")
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
                job.updated_at = datetime.utcnow()
                session.add(job)
                await session.commit()

                proc = await asyncio.create_subprocess_exec(
                    "skill-seekers", "create", repo,
                    "--output", repo_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()

                if proc.returncode != 0:
                    error_msg = stderr.decode("utf-8", errors="replace")[:500]
                    raise RuntimeError(f"skill-seekers create failed for {repo}: {error_msg}")

                logger.info("skill_seekers_create_done", repo=repo, dir=repo_dir)

                # Step 2 (optional): Enhance
                if job.enhance:
                    job.current_step = f"enhancing {repo}"
                    step += 1
                    job.progress = int((step / total_steps) * 100)
                    job.updated_at = datetime.utcnow()
                    session.add(job)
                    await session.commit()

                    proc = await asyncio.create_subprocess_exec(
                        "skill-seekers", "enhance", repo_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
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
                    job.updated_at = datetime.utcnow()
                    session.add(job)
                    await session.commit()

                    out_filename = f"{slug}_{target}.md"
                    out_path = os.path.join(output_dir, out_filename)

                    proc = await asyncio.create_subprocess_exec(
                        "skill-seekers", "package", repo_dir,
                        "--target", target,
                        "--output", out_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()

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
        output_dir = tempfile.mkdtemp(prefix="skill_seekers_mock_")
        output_files: list[str] = []
        total_steps = len(repos) * len(targets)
        step = 0

        for repo in repos:
            slug = self._repo_slug(repo)

            # Simulate scraping
            job.current_step = f"scraping {repo} (mock)"
            job.progress = int(((step + 0.5) / total_steps) * 80)
            job.updated_at = datetime.utcnow()
            session.add(job)
            await session.commit()
            await asyncio.sleep(1.5)

            # Simulate enhance
            if job.enhance:
                job.current_step = f"enhancing {repo} (mock)"
                job.updated_at = datetime.utcnow()
                session.add(job)
                await session.commit()
                await asyncio.sleep(1.0)

            for target in targets:
                job.current_step = f"packaging {repo} for {target} (mock)"
                step += 1
                job.progress = int((step / total_steps) * 90)
                job.updated_at = datetime.utcnow()
                session.add(job)
                await session.commit()
                await asyncio.sleep(0.5)

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
                    f"Generated: {datetime.utcnow().isoformat()}\n"
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
    ) -> tuple[list[ScrapeJob], int]:
        """List scrape jobs for a user with pagination."""
        count_result = await session.execute(
            select(func.count()).select_from(ScrapeJob).where(
                ScrapeJob.user_id == user_id
            )
        )
        total = count_result.scalar_one()

        result = await session.execute(
            select(ScrapeJob)
            .where(ScrapeJob.user_id == user_id)
            .order_by(ScrapeJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        jobs = list(result.scalars().all())

        return jobs, total

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

        files = json.loads(job.output_files_json)
        for filepath in files:
            if os.path.basename(filepath) == filename and os.path.isfile(filepath):
                return filepath

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
