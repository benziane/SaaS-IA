import { BaseAPI } from "./base";
import {
  Dataset,
  DataAnalysis,
  DataAskRequest,
  DataAskResponse,
  DataReportResponse,
  PaginationParams,
} from "../types";

/**
 * Data Analyst API — CSV/JSON/Excel analysis with DuckDB, natural language
 * queries, auto-analysis, and comprehensive reports.
 */
export class DataAnalystAPI extends BaseAPI {
  // -- Datasets ------------------------------------------------------------

  /** Upload a dataset (CSV, JSON, or Excel). */
  async uploadDataset(file: Blob | File): Promise<Dataset> {
    const form = new FormData();
    form.append("file", file);
    return this._request<Dataset>("/api/data/datasets", {
      method: "POST",
      body: form,
    });
  }

  /** List datasets. */
  async listDatasets(params?: PaginationParams): Promise<Dataset[]> {
    return this._get<Dataset[]>("/api/data/datasets", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get dataset with preview. */
  async getDataset(id: string): Promise<Dataset> {
    return this._get<Dataset>(`/api/data/datasets/${id}`);
  }

  /** Delete a dataset and its analyses. */
  async deleteDataset(id: string): Promise<void> {
    return this._delete(`/api/data/datasets/${id}`);
  }

  // -- Analysis ------------------------------------------------------------

  /** Ask a natural language question about a dataset. */
  async ask(datasetId: string, data: DataAskRequest): Promise<DataAskResponse> {
    return this._post<DataAskResponse>(`/api/data/datasets/${datasetId}/ask`, data);
  }

  /** Run automatic analysis on a dataset. */
  async autoAnalyze(datasetId: string): Promise<DataAnalysis> {
    return this._post<DataAnalysis>(`/api/data/datasets/${datasetId}/auto-analyze`);
  }

  /** Generate a comprehensive report for a dataset. */
  async report(datasetId: string): Promise<DataReportResponse> {
    return this._post<DataReportResponse>(`/api/data/datasets/${datasetId}/report`);
  }

  /** List analyses for a dataset. */
  async listAnalyses(datasetId: string, params?: PaginationParams): Promise<DataAnalysis[]> {
    return this._get<DataAnalysis[]>(`/api/data/datasets/${datasetId}/analyses`, {
      limit: params?.limit,
      offset: params?.offset,
    });
  }
}
