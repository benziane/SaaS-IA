/**
 * SaaSIAClient — main entry point for the SaaS-IA TypeScript SDK.
 *
 * Usage:
 * ```ts
 * const client = new SaaSIAClient({ baseUrl: "http://localhost:8004" });
 * await client.login("user@example.com", "password");
 *
 * const transcriptions = await client.transcription.list();
 * const result = await client.knowledge.ask({ question: "What is …?" });
 * ```
 */

import { SaaSIAClientOptions, LoginResponse, UserProfile } from "./types";
import { BaseAPI, SaaSIAError } from "./api/base";

// Module APIs
import { TranscriptionAPI } from "./api/transcription";
import { ConversationAPI } from "./api/conversation";
import { KnowledgeAPI } from "./api/knowledge";
import { ContentStudioAPI } from "./api/content-studio";
import { PipelineAPI } from "./api/pipelines";
import { AgentAPI } from "./api/agents";
import { CompareAPI } from "./api/compare";
import { SentimentAPI } from "./api/sentiment";
import { ImageGenAPI } from "./api/image-gen";
import { VideoGenAPI } from "./api/video-gen";
import { ChatbotAPI } from "./api/chatbot";
import { MarketplaceAPI } from "./api/marketplace";
import { DataAnalystAPI } from "./api/data-analyst";
import { PDFAPI } from "./api/pdf";
import { SocialPublisherAPI } from "./api/social-publisher";
import { FormsAPI } from "./api/forms";
import { CodeSandboxAPI } from "./api/code-sandbox";
import { PresentationGenAPI } from "./api/presentation-gen";
import { AudioStudioAPI } from "./api/audio-studio";

const DEFAULT_BASE_URL = "http://localhost:8004";
const DEFAULT_TIMEOUT = 30_000;

export class SaaSIAClient {
  private baseUrl: string;
  private apiKey?: string;
  private token?: string;
  private timeout: number;

  // Lazily-created module API instances
  private _transcription?: TranscriptionAPI;
  private _conversation?: ConversationAPI;
  private _knowledge?: KnowledgeAPI;
  private _contentStudio?: ContentStudioAPI;
  private _pipelines?: PipelineAPI;
  private _agents?: AgentAPI;
  private _compare?: CompareAPI;
  private _sentiment?: SentimentAPI;
  private _imageGen?: ImageGenAPI;
  private _videoGen?: VideoGenAPI;
  private _chatbot?: ChatbotAPI;
  private _marketplace?: MarketplaceAPI;
  private _dataAnalyst?: DataAnalystAPI;
  private _pdf?: PDFAPI;
  private _socialPublisher?: SocialPublisherAPI;
  private _forms?: FormsAPI;
  private _codeSandbox?: CodeSandboxAPI;
  private _presentationGen?: PresentationGenAPI;
  private _audioStudio?: AudioStudioAPI;

  constructor(options: SaaSIAClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.apiKey = options.apiKey;
    this.timeout = options.timeout ?? DEFAULT_TIMEOUT;
  }

  // -- Auth ----------------------------------------------------------------

  /**
   * Authenticate with email & password.  The returned JWT is stored
   * internally and used for all subsequent requests.
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const res = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });

    if (!res.ok) {
      let detail: string;
      try {
        const err = await res.json();
        detail = err.detail ?? res.statusText;
      } catch {
        detail = res.statusText;
      }
      throw new SaaSIAError(res.status, detail);
    }

    const data: LoginResponse = await res.json();
    this.token = data.access_token;
    // Propagate to existing API instances
    this._propagateAuth();
    return data;
  }

  /**
   * Set a pre-existing JWT token (e.g. from a refresh or external auth).
   */
  setToken(token: string): void {
    this.token = token;
    this._propagateAuth();
  }

  /**
   * Set an API key for Public API v1 endpoints.
   */
  setApiKey(key: string): void {
    this.apiKey = key;
    this._propagateAuth();
  }

  /**
   * Get the current user profile.
   */
  async me(): Promise<UserProfile> {
    return this._baseRequest<UserProfile>("/api/auth/me");
  }

  // -- Module namespaces ---------------------------------------------------

  get transcription(): TranscriptionAPI {
    if (!this._transcription) {
      this._transcription = this._createApi(TranscriptionAPI);
    }
    return this._transcription;
  }

  get conversation(): ConversationAPI {
    if (!this._conversation) {
      this._conversation = this._createApi(ConversationAPI);
    }
    return this._conversation;
  }

  get knowledge(): KnowledgeAPI {
    if (!this._knowledge) {
      this._knowledge = this._createApi(KnowledgeAPI);
    }
    return this._knowledge;
  }

  get contentStudio(): ContentStudioAPI {
    if (!this._contentStudio) {
      this._contentStudio = this._createApi(ContentStudioAPI);
    }
    return this._contentStudio;
  }

  get pipelines(): PipelineAPI {
    if (!this._pipelines) {
      this._pipelines = this._createApi(PipelineAPI);
    }
    return this._pipelines;
  }

  get agents(): AgentAPI {
    if (!this._agents) {
      this._agents = this._createApi(AgentAPI);
    }
    return this._agents;
  }

  get compare(): CompareAPI {
    if (!this._compare) {
      this._compare = this._createApi(CompareAPI);
    }
    return this._compare;
  }

  get sentiment(): SentimentAPI {
    if (!this._sentiment) {
      this._sentiment = this._createApi(SentimentAPI);
    }
    return this._sentiment;
  }

  get imageGen(): ImageGenAPI {
    if (!this._imageGen) {
      this._imageGen = this._createApi(ImageGenAPI);
    }
    return this._imageGen;
  }

  get videoGen(): VideoGenAPI {
    if (!this._videoGen) {
      this._videoGen = this._createApi(VideoGenAPI);
    }
    return this._videoGen;
  }

  get chatbot(): ChatbotAPI {
    if (!this._chatbot) {
      this._chatbot = this._createApi(ChatbotAPI);
    }
    return this._chatbot;
  }

  get marketplace(): MarketplaceAPI {
    if (!this._marketplace) {
      this._marketplace = this._createApi(MarketplaceAPI);
    }
    return this._marketplace;
  }

  get dataAnalyst(): DataAnalystAPI {
    if (!this._dataAnalyst) {
      this._dataAnalyst = this._createApi(DataAnalystAPI);
    }
    return this._dataAnalyst;
  }

  get pdf(): PDFAPI {
    if (!this._pdf) {
      this._pdf = this._createApi(PDFAPI);
    }
    return this._pdf;
  }

  get socialPublisher(): SocialPublisherAPI {
    if (!this._socialPublisher) {
      this._socialPublisher = this._createApi(SocialPublisherAPI);
    }
    return this._socialPublisher;
  }

  get forms(): FormsAPI {
    if (!this._forms) {
      this._forms = this._createApi(FormsAPI);
    }
    return this._forms;
  }

  get codeSandbox(): CodeSandboxAPI {
    if (!this._codeSandbox) {
      this._codeSandbox = this._createApi(CodeSandboxAPI);
    }
    return this._codeSandbox;
  }

  get presentationGen(): PresentationGenAPI {
    if (!this._presentationGen) {
      this._presentationGen = this._createApi(PresentationGenAPI);
    }
    return this._presentationGen;
  }

  get audioStudio(): AudioStudioAPI {
    if (!this._audioStudio) {
      this._audioStudio = this._createApi(AudioStudioAPI);
    }
    return this._audioStudio;
  }

  // -- Internals -----------------------------------------------------------

  private _createApi<T extends BaseAPI>(
    ApiClass: new (baseUrl: string, timeout: number) => T
  ): T {
    const api = new ApiClass(this.baseUrl, this.timeout);
    if (this.token) api._setToken(this.token);
    if (this.apiKey) api._setApiKey(this.apiKey);
    return api;
  }

  private _propagateAuth(): void {
    const apis: (BaseAPI | undefined)[] = [
      this._transcription,
      this._conversation,
      this._knowledge,
      this._contentStudio,
      this._pipelines,
      this._agents,
      this._compare,
      this._sentiment,
      this._imageGen,
      this._videoGen,
      this._chatbot,
      this._marketplace,
      this._dataAnalyst,
      this._pdf,
      this._socialPublisher,
      this._forms,
      this._codeSandbox,
      this._presentationGen,
      this._audioStudio,
    ];

    for (const api of apis) {
      if (!api) continue;
      if (this.token) api._setToken(this.token);
      if (this.apiKey) api._setApiKey(this.apiKey);
    }
  }

  /** Simple GET helper used by the client itself (e.g. `me()`). */
  private async _baseRequest<T>(path: string): Promise<T> {
    const headers: Record<string, string> = {};
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
    if (this.apiKey) headers["X-API-Key"] = this.apiKey;

    const res = await fetch(`${this.baseUrl}${path}`, { headers });
    if (!res.ok) {
      let detail: string;
      try {
        const err = await res.json();
        detail = err.detail ?? res.statusText;
      } catch {
        detail = res.statusText;
      }
      throw new SaaSIAError(res.status, detail);
    }
    return (await res.json()) as T;
  }
}
