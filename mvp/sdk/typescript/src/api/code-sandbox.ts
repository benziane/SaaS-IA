import { BaseAPI } from "./base";
import {
  Sandbox,
  SandboxCreateRequest,
  SandboxCell,
  CodeGenerateRequest,
  CodeGenerateResponse,
  CodeExplainRequest,
  CodeDebugRequest,
  PaginationParams,
} from "../types";

/**
 * Code Sandbox API — secure code execution, AI code generation,
 * explanation, and debugging.
 */
export class CodeSandboxAPI extends BaseAPI {
  // -- Sandboxes -----------------------------------------------------------

  /** Create a sandbox. */
  async create(data: SandboxCreateRequest): Promise<Sandbox> {
    return this._post<Sandbox>("/api/sandbox/sandboxes", data);
  }

  /** List sandboxes. */
  async list(params?: PaginationParams): Promise<Sandbox[]> {
    return this._get<Sandbox[]>("/api/sandbox/sandboxes", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get sandbox with cells. */
  async get(id: string): Promise<Sandbox> {
    return this._get<Sandbox>(`/api/sandbox/sandboxes/${id}`);
  }

  /** Delete a sandbox. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/sandbox/sandboxes/${id}`);
  }

  // -- Cells ---------------------------------------------------------------

  /** Add a cell to a sandbox. */
  async addCell(sandboxId: string, data: { source: string; order?: number }): Promise<SandboxCell> {
    return this._post<SandboxCell>(`/api/sandbox/sandboxes/${sandboxId}/cells`, data);
  }

  /** Update cell source code. */
  async updateCell(sandboxId: string, cellId: string, data: { source: string }): Promise<SandboxCell> {
    return this._put<SandboxCell>(`/api/sandbox/sandboxes/${sandboxId}/cells/${cellId}`, data);
  }

  /** Remove a cell. */
  async removeCell(sandboxId: string, cellId: string): Promise<void> {
    return this._delete(`/api/sandbox/sandboxes/${sandboxId}/cells/${cellId}`);
  }

  /** Execute a cell. */
  async executeCell(sandboxId: string, cellId: string): Promise<SandboxCell> {
    return this._post<SandboxCell>(`/api/sandbox/sandboxes/${sandboxId}/cells/${cellId}/execute`);
  }

  // -- AI code tools -------------------------------------------------------

  /** Generate code from a natural language prompt. */
  async generate(data: CodeGenerateRequest): Promise<CodeGenerateResponse> {
    return this._post<CodeGenerateResponse>("/api/sandbox/generate", data);
  }

  /** Explain code with AI. */
  async explain(data: CodeExplainRequest): Promise<{ explanation: string }> {
    return this._post<{ explanation: string }>("/api/sandbox/explain", data);
  }

  /** Debug code with AI. */
  async debug(data: CodeDebugRequest): Promise<{ fix: string; explanation: string }> {
    return this._post<{ fix: string; explanation: string }>("/api/sandbox/debug", data);
  }
}
