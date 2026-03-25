"""
LangGraph-style Agent Graph Engine - Stateful agent execution with reflection loops.

Provides ReAct pattern, plan-and-execute, and reflection loops
inspired by LangGraph (10K+ stars).

Uses our existing AIAssistantService and tool executor.
Falls back gracefully to the existing sequential planner if not needed.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog

logger = structlog.get_logger()


class AgentState:
    """Stateful agent blackboard - accumulates context between steps."""

    def __init__(self, instruction: str, user_id: Optional[UUID] = None):
        self.instruction = instruction
        self.user_id = user_id
        self.steps_completed: list[dict] = []
        self.current_output: str = ""
        self.reflections: list[str] = []
        self.iteration: int = 0
        self.max_iterations: int = 5
        self.finished: bool = False
        self.error: Optional[str] = None

    def add_step(self, action: str, output: str, tool_used: Optional[str] = None):
        self.steps_completed.append({
            "action": action,
            "output": output[:3000],
            "tool_used": tool_used,
            "iteration": self.iteration,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.current_output = output

    def add_reflection(self, reflection: str):
        self.reflections.append(reflection)

    def get_context(self) -> str:
        """Build context string from accumulated state."""
        parts = [f"Original instruction: {self.instruction}"]
        if self.steps_completed:
            parts.append("Steps completed so far:")
            for s in self.steps_completed[-5:]:  # Last 5 steps only
                parts.append(f"  [{s['action']}]: {s['output'][:500]}")
        if self.reflections:
            parts.append(f"Reflections: {'; '.join(self.reflections[-3:])}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "instruction": self.instruction,
            "steps_completed": self.steps_completed,
            "current_output": self.current_output[:2000],
            "reflections": self.reflections,
            "iteration": self.iteration,
            "finished": self.finished,
            "error": self.error,
        }


async def run_react_agent(
    instruction: str,
    user_id: Optional[UUID] = None,
    max_iterations: int = 5,
    provider: str = "gemini",
) -> dict:
    """Run an agent using the ReAct (Reason + Act) pattern.

    Loop: Think -> Act -> Observe -> Think -> ... until done.
    """
    from app.modules.agents.executor import execute_step

    state = AgentState(instruction, user_id)
    state.max_iterations = max_iterations

    for i in range(max_iterations):
        state.iteration = i + 1

        # THINK: ask LLM what to do next
        think_result = await _think(state, provider)

        if think_result.get("finished"):
            state.finished = True
            state.current_output = think_result.get("final_answer", state.current_output)
            break

        # ACT: execute the decided action
        action = think_result.get("action", "generate_text")
        action_input = think_result.get("action_input", {})
        if user_id:
            action_input["_user_id"] = str(user_id)

        try:
            result = await execute_step(
                action=action,
                input_data=action_input,
                previous_output=state.current_output,
            )
            output = result.get("output", "")
            state.add_step(action, output, tool_used=action)
        except Exception as e:
            state.add_step(action, f"Error: {str(e)[:500]}")
            state.error = str(e)[:500]

        # OBSERVE + REFLECT (optional)
        if i > 0 and i % 2 == 0:
            reflection = await _reflect(state, provider)
            if reflection:
                state.add_reflection(reflection)

    if not state.finished:
        state.finished = True

    logger.info(
        "react_agent_complete",
        iterations=state.iteration,
        steps=len(state.steps_completed),
        reflections=len(state.reflections),
    )

    return state.to_dict()


async def _think(state: AgentState, provider: str) -> dict:
    """LLM reasoning step: decide what to do next."""
    from app.ai_assistant.service import AIAssistantService
    from app.modules.agents.planner import AVAILABLE_ACTIONS

    actions_desc = "\n".join(f"- {k}: {v}" for k, v in list(AVAILABLE_ACTIONS.items())[:15])

    prompt = f"""You are an AI agent using the ReAct framework. Based on the current state, decide the next action.

{state.get_context()}

Available actions:
{actions_desc}

If you have enough information to answer the original instruction, respond with:
{{"finished": true, "final_answer": "your complete answer"}}

Otherwise, respond with:
{{"finished": false, "action": "action_name", "action_input": {{"key": "value"}}, "reasoning": "why this action"}}

Respond ONLY with JSON."""

    try:
        result = await AIAssistantService.process_text_with_provider(
            text=prompt, task="agent_reasoning", provider_name=provider,
            user_id=state.user_id, module="agents",
        )
        text = result.get("processed_text", "{}")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        logger.warning("react_think_failed", error=str(e))

    return {"finished": True, "final_answer": state.current_output or "Unable to complete the task."}


async def _reflect(state: AgentState, provider: str) -> Optional[str]:
    """Self-reflection step: evaluate progress and suggest corrections."""
    from app.ai_assistant.service import AIAssistantService

    prompt = f"""Review the progress of this AI agent task and provide a brief reflection.

Original task: {state.instruction}
Steps completed: {len(state.steps_completed)}
Current output preview: {state.current_output[:1000]}

In 1-2 sentences: Is the agent making good progress? What should it focus on next? Any mistakes to correct?"""

    try:
        result = await AIAssistantService.process_text_with_provider(
            text=prompt, task="reflection", provider_name=provider,
            user_id=state.user_id, module="agents",
        )
        return result.get("processed_text", "")[:500]
    except Exception:
        return None
