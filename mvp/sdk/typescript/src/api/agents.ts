import { BaseAPI } from "./base";
import {
  AgentRun,
  AgentRunRequest,
  AgentReactRequest,
  PaginationParams,
} from "../types";

/**
 * Agents API — autonomous AI agents with planning and 65+ available actions.
 */
export class AgentAPI extends BaseAPI {
  /** Execute an autonomous AI agent with a goal. */
  async run(data: AgentRunRequest): Promise<AgentRun> {
    return this._post<AgentRun>("/api/agents/run", data);
  }

  /** Run a ReAct agent (reason + act loop). */
  async react(data: AgentReactRequest): Promise<AgentRun> {
    return this._post<AgentRun>("/api/agents/react", data);
  }

  /** List past agent runs. */
  async listRuns(params?: PaginationParams): Promise<AgentRun[]> {
    return this._get<AgentRun[]>("/api/agents/runs", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get agent run details with step history. */
  async getRun(id: string): Promise<AgentRun> {
    return this._get<AgentRun>(`/api/agents/runs/${id}`);
  }

  /** Cancel a running agent. */
  async cancelRun(id: string): Promise<{ status: string }> {
    return this._post<{ status: string }>(`/api/agents/runs/${id}/cancel`);
  }
}
