/**
 * BaseAPI — shared HTTP helper used by every module API class.
 *
 * Handles authentication headers, error normalisation, and JSON
 * serialisation so that concrete API classes only declare endpoints.
 */

import { ApiError } from "../types";

export interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
  /** When true the raw Response is returned instead of parsed JSON. */
  raw?: boolean;
}

export class SaaSIAError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`SaaS-IA API error ${status}: ${detail}`);
    this.name = "SaaSIAError";
    this.status = status;
    this.detail = detail;
  }
}

export class BaseAPI {
  /** @internal */ _baseUrl: string;
  /** @internal */ _apiKey?: string;
  /** @internal */ _token?: string;
  /** @internal */ _timeout: number;

  constructor(baseUrl: string, timeout: number) {
    this._baseUrl = baseUrl.replace(/\/+$/, "");
    this._timeout = timeout;
  }

  // -- auth helpers (set by SaaSIAClient) ----------------------------------

  /** @internal */
  _setToken(token: string): void {
    this._token = token;
  }

  /** @internal */
  _setApiKey(key: string): void {
    this._apiKey = key;
  }

  // -- HTTP primitives -----------------------------------------------------

  protected async _request<T = unknown>(
    path: string,
    opts: RequestOptions = {}
  ): Promise<T> {
    const { method = "GET", body, query, headers = {}, raw = false } = opts;

    // Build URL with query params
    let url = `${this._baseUrl}${path}`;
    if (query) {
      const params = new URLSearchParams();
      for (const [k, v] of Object.entries(query)) {
        if (v !== undefined && v !== null) {
          params.append(k, String(v));
        }
      }
      const qs = params.toString();
      if (qs) url += `?${qs}`;
    }

    // Auth headers
    const reqHeaders: Record<string, string> = {
      ...headers,
    };
    if (this._token) {
      reqHeaders["Authorization"] = `Bearer ${this._token}`;
    }
    if (this._apiKey) {
      reqHeaders["X-API-Key"] = this._apiKey;
    }

    // Body
    let reqBody: string | FormData | undefined;
    if (body !== undefined) {
      if (body instanceof FormData) {
        reqBody = body;
        // Let the runtime set Content-Type with boundary
      } else {
        reqHeaders["Content-Type"] = "application/json";
        reqBody = JSON.stringify(body);
      }
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this._timeout);

    let response: Response;
    try {
      response = await fetch(url, {
        method,
        headers: reqHeaders,
        body: reqBody,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      let detail: string;
      try {
        const err: ApiError = await response.json();
        detail = err.detail ?? response.statusText;
      } catch {
        detail = response.statusText;
      }
      throw new SaaSIAError(response.status, detail);
    }

    if (raw) {
      return response as unknown as T;
    }

    // 204 No Content
    if (response.status === 204) {
      return undefined as unknown as T;
    }

    return (await response.json()) as T;
  }

  protected _get<T>(path: string, query?: Record<string, string | number | boolean | undefined>): Promise<T> {
    return this._request<T>(path, { query });
  }

  protected _post<T>(path: string, body?: unknown, query?: Record<string, string | number | boolean | undefined>): Promise<T> {
    return this._request<T>(path, { method: "POST", body, query });
  }

  protected _put<T>(path: string, body?: unknown): Promise<T> {
    return this._request<T>(path, { method: "PUT", body });
  }

  protected _patch<T>(path: string, body?: unknown): Promise<T> {
    return this._request<T>(path, { method: "PATCH", body });
  }

  protected _delete<T = void>(path: string): Promise<T> {
    return this._request<T>(path, { method: "DELETE" });
  }
}
