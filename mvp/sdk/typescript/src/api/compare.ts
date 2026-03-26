import { BaseAPI } from "./base";
import {
  CompareRunRequest,
  CompareResult,
  CompareVoteRequest,
  CompareStats,
} from "../types";

/**
 * Compare API — run a prompt across multiple AI providers and vote for the
 * best response.
 */
export class CompareAPI extends BaseAPI {
  /** Run a prompt across multiple providers. */
  async run(data: CompareRunRequest): Promise<CompareResult> {
    return this._post<CompareResult>("/api/compare/run", data);
  }

  /** Vote for the best provider response. */
  async vote(comparisonId: string, data: CompareVoteRequest): Promise<{ status: string }> {
    return this._post<{ status: string }>(`/api/compare/${comparisonId}/vote`, data);
  }

  /** Get aggregated provider quality stats. */
  async stats(): Promise<CompareStats> {
    return this._get<CompareStats>("/api/compare/stats");
  }
}
