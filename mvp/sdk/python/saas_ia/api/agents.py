"""Agents API — autonomous AI agents with planning and 65+ actions."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class AgentAPI(BaseAPI):
    """Wraps ``/api/agents`` endpoints."""

    async def run(
        self,
        goal: str,
        *,
        context: str | None = None,
        max_steps: int | None = None,
    ) -> dict[str, Any]:
        """Execute an autonomous AI agent with a goal."""
        body: dict[str, Any] = {"goal": goal}
        if context:
            body["context"] = context
        if max_steps:
            body["max_steps"] = max_steps
        return await self._post("/api/agents/run", json=body)

    async def react(
        self,
        instruction: str,
        *,
        context: str | None = None,
        max_iterations: int | None = None,
    ) -> dict[str, Any]:
        """Run a ReAct agent (reason + act loop)."""
        body: dict[str, Any] = {"instruction": instruction}
        if context:
            body["context"] = context
        if max_iterations:
            body["max_iterations"] = max_iterations
        return await self._post("/api/agents/react", json=body)

    async def list_runs(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List past agent runs."""
        return await self._get(
            "/api/agents/runs",
            params={"limit": limit, "offset": offset},
        )

    async def get_run(self, run_id: str) -> dict[str, Any]:
        """Get agent run details with step history."""
        return await self._get(f"/api/agents/runs/{run_id}")

    async def cancel_run(self, run_id: str) -> dict[str, Any]:
        """Cancel a running agent."""
        return await self._post(f"/api/agents/runs/{run_id}/cancel")
