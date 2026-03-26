import { BaseAPI } from "./base";
import {
  Pipeline,
  PipelineCreateRequest,
  PipelineUpdateRequest,
  PipelineExecution,
  PipelineExecuteRequest,
  PaginationParams,
} from "../types";

/**
 * Pipelines API — sequential AI operation chaining with 23 step types.
 */
export class PipelineAPI extends BaseAPI {
  // -- CRUD ----------------------------------------------------------------

  /** Create a pipeline. */
  async create(data: PipelineCreateRequest): Promise<Pipeline> {
    return this._post<Pipeline>("/api/pipelines/", data);
  }

  /** List pipelines. */
  async list(params?: PaginationParams): Promise<Pipeline[]> {
    return this._get<Pipeline[]>("/api/pipelines/", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get pipeline by ID. */
  async get(id: string): Promise<Pipeline> {
    return this._get<Pipeline>(`/api/pipelines/${id}`);
  }

  /** Update a pipeline. */
  async update(id: string, data: PipelineUpdateRequest): Promise<Pipeline> {
    return this._put<Pipeline>(`/api/pipelines/${id}`, data);
  }

  /** Delete a pipeline. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/pipelines/${id}`);
  }

  // -- Execution -----------------------------------------------------------

  /** Execute a pipeline with input data. */
  async execute(id: string, data: PipelineExecuteRequest): Promise<PipelineExecution> {
    return this._post<PipelineExecution>(`/api/pipelines/${id}/execute`, data);
  }

  /** List executions for a pipeline. */
  async listExecutions(pipelineId: string, params?: PaginationParams): Promise<PipelineExecution[]> {
    return this._get<PipelineExecution[]>(`/api/pipelines/${pipelineId}/executions`, {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get execution details by ID. */
  async getExecution(executionId: string): Promise<PipelineExecution> {
    return this._get<PipelineExecution>(`/api/pipelines/executions/${executionId}`);
  }
}
