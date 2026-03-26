/**
 * @saas-ia/sdk — Official SaaS-IA TypeScript SDK
 *
 * @example
 * ```ts
 * import { SaaSIAClient } from "@saas-ia/sdk";
 *
 * const client = new SaaSIAClient({ baseUrl: "http://localhost:8004" });
 * await client.login("user@example.com", "password");
 *
 * // Transcribe a YouTube video
 * const job = await client.transcription.create({
 *   source_url: "https://youtube.com/watch?v=...",
 * });
 *
 * // Ask a question to your knowledge base
 * const answer = await client.knowledge.ask({
 *   question: "What are the key takeaways?",
 * });
 * ```
 */

export { SaaSIAClient } from "./client";
export { SaaSIAError } from "./api/base";

// Module APIs (for advanced users who want to construct them manually)
export { TranscriptionAPI } from "./api/transcription";
export { ConversationAPI } from "./api/conversation";
export { KnowledgeAPI } from "./api/knowledge";
export { ContentStudioAPI } from "./api/content-studio";
export { PipelineAPI } from "./api/pipelines";
export { AgentAPI } from "./api/agents";
export { CompareAPI } from "./api/compare";
export { SentimentAPI } from "./api/sentiment";
export { ImageGenAPI } from "./api/image-gen";
export { VideoGenAPI } from "./api/video-gen";
export { ChatbotAPI } from "./api/chatbot";
export { MarketplaceAPI } from "./api/marketplace";
export { DataAnalystAPI } from "./api/data-analyst";
export { PDFAPI } from "./api/pdf";
export { SocialPublisherAPI } from "./api/social-publisher";
export { FormsAPI } from "./api/forms";
export { CodeSandboxAPI } from "./api/code-sandbox";
export { PresentationGenAPI } from "./api/presentation-gen";
export { AudioStudioAPI } from "./api/audio-studio";

// Types
export * from "./types";
