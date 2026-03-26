// ============================================================================
// SaaS-IA SDK — TypeScript type definitions
// Generated from backend Pydantic schemas and API reference
// ============================================================================

// ---------------------------------------------------------------------------
// Common
// ---------------------------------------------------------------------------

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface ApiError {
  detail: string;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Transcription
// ---------------------------------------------------------------------------

export interface Transcription {
  id: string;
  user_id: string;
  source_url: string | null;
  title: string | null;
  status: "pending" | "processing" | "completed" | "failed";
  language: string | null;
  duration_seconds: number | null;
  text: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranscriptionCreateRequest {
  source_url: string;
  language?: string;
}

export interface SmartTranscribeRequest {
  source_url: string;
  language?: string;
  enable_diarization?: boolean;
}

export interface SmartTranscribeResponse {
  job_id: string;
  status: string;
  text: string | null;
  segments: TranscriptSegment[];
  provider: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string;
}

export interface SpeakerUtterance {
  speaker: string;
  start: number;
  end: number;
  text: string;
}

export interface TranscriptionWithSpeakers {
  id: string;
  text: string;
  speakers: SpeakerUtterance[];
}

export interface Chapter {
  title: string;
  start_time: number;
  end_time: number;
  summary: string;
}

export interface Summary {
  transcription_id: string;
  style: string;
  summary: string;
}

export interface Keyword {
  keyword: string;
  relevance: number;
  count: number;
}

export interface SearchTranscriptionResult {
  transcription_id: string;
  title: string | null;
  snippet: string;
  score: number;
}

export interface BatchTranscribeResponse {
  job_ids: string[];
  total: number;
}

export interface YouTubeMetadata {
  title: string;
  description: string;
  channel: string;
  duration: number;
  view_count: number;
  thumbnail_url: string | null;
}

export interface PlaylistTranscribeRequest {
  playlist_url: string;
  language?: string;
  max_videos?: number;
}

export interface PlaylistTranscribeResponse {
  playlist_id: string;
  results: Array<{ video_url: string; job_id: string; status: string }>;
  total: number;
}

export interface LiveStreamStatusResponse {
  url: string;
  is_live: boolean;
  title: string | null;
}

export interface LiveStreamCaptureRequest {
  url: string;
  duration_seconds?: number;
}

export interface LiveStreamCaptureResponse {
  job_id: string;
  status: string;
}

export interface VideoAnalyzeRequest {
  source_url: string;
  interval_seconds?: number;
  max_frames?: number;
}

export interface VideoAnalyzeResponse {
  frames: Array<{ timestamp: number; description: string }>;
  summary: string;
}

// ---------------------------------------------------------------------------
// Conversation
// ---------------------------------------------------------------------------

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  transcription_id: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface ConversationCreateRequest {
  transcription_id?: string;
}

export interface MessageCreateRequest {
  content: string;
}

// ---------------------------------------------------------------------------
// Knowledge Base
// ---------------------------------------------------------------------------

export interface Document {
  id: string;
  filename: string;
  content_type: string;
  total_chunks: number;
  status: string;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
}

export interface KnowledgeSearchRequest {
  query: string;
  limit?: number;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  content: string;
  score: number;
  chunk_index: number;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: KnowledgeSearchResult[];
  total: number;
}

export interface AskRequest {
  question: string;
  limit?: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: KnowledgeSearchResult[];
  provider: string;
}

export interface SearchStatus {
  tfidf: boolean;
  vector: boolean;
  hybrid: boolean;
  default_mode: string;
}

// ---------------------------------------------------------------------------
// Content Studio
// ---------------------------------------------------------------------------

export type ContentFormat =
  | "blog_post"
  | "social_media"
  | "email"
  | "newsletter"
  | "press_release"
  | "landing_page"
  | "product_description"
  | "video_script"
  | "podcast_notes"
  | "technical_doc";

export interface ContentProject {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  source_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentPiece {
  id: string;
  project_id: string;
  format: ContentFormat;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ContentProjectCreateRequest {
  title: string;
  description?: string;
  source_text?: string;
}

export interface ContentGenerateRequest {
  formats: ContentFormat[];
  tone?: string;
  language?: string;
}

export interface ContentFromUrlRequest {
  url: string;
  formats: ContentFormat[];
  tone?: string;
}

// ---------------------------------------------------------------------------
// Pipelines
// ---------------------------------------------------------------------------

export interface Pipeline {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  steps: PipelineStep[];
  created_at: string;
  updated_at: string;
}

export interface PipelineStep {
  type: string;
  config: Record<string, unknown>;
  order: number;
}

export interface PipelineCreateRequest {
  name: string;
  description?: string;
  steps: PipelineStep[];
}

export interface PipelineUpdateRequest {
  name?: string;
  description?: string;
  steps?: PipelineStep[];
}

export interface PipelineExecution {
  id: string;
  pipeline_id: string;
  status: "pending" | "running" | "completed" | "failed";
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface PipelineExecuteRequest {
  input_data: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Agents
// ---------------------------------------------------------------------------

export interface AgentRun {
  id: string;
  user_id: string;
  goal: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  result: string | null;
  steps: AgentStep[];
  created_at: string;
  completed_at: string | null;
}

export interface AgentStep {
  action: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  status: string;
  timestamp: string;
}

export interface AgentRunRequest {
  goal: string;
  context?: string;
  max_steps?: number;
}

export interface AgentReactRequest {
  instruction: string;
  context?: string;
  max_iterations?: number;
}

// ---------------------------------------------------------------------------
// Compare
// ---------------------------------------------------------------------------

export interface CompareRunRequest {
  prompt: string;
  providers?: string[];
}

export interface CompareResult {
  id: string;
  prompt: string;
  responses: ProviderResponse[];
  created_at: string;
}

export interface ProviderResponse {
  provider: string;
  model: string;
  response: string;
  latency_ms: number;
  token_count: number;
}

export interface CompareVoteRequest {
  winner_provider: string;
}

export interface CompareStats {
  total_comparisons: number;
  provider_stats: Record<string, { wins: number; avg_latency_ms: number }>;
}

// ---------------------------------------------------------------------------
// Sentiment
// ---------------------------------------------------------------------------

export interface SentimentAnalyzeRequest {
  text: string;
}

export interface SentimentResult {
  label: string;
  score: number;
  emotions: Record<string, number>;
  provider: string;
}

export interface SentimentTranscriptionRequest {
  transcription_id: string;
}

// ---------------------------------------------------------------------------
// Image Gen
// ---------------------------------------------------------------------------

export type ImageStyle =
  | "realistic"
  | "cartoon"
  | "watercolor"
  | "oil_painting"
  | "sketch"
  | "pixel_art"
  | "anime"
  | "3d_render"
  | "minimalist"
  | "abstract";

export interface GeneratedImage {
  id: string;
  user_id: string;
  prompt: string;
  style: ImageStyle;
  image_url: string | null;
  width: number;
  height: number;
  created_at: string;
}

export interface ImageGenerateRequest {
  prompt: string;
  style?: ImageStyle;
  width?: number;
  height?: number;
}

export interface ImageThumbnailRequest {
  title: string;
  style?: ImageStyle;
  transcription_id?: string;
}

export interface ImageBulkRequest {
  prompts: Array<{ prompt: string; style?: ImageStyle }>;
}

// ---------------------------------------------------------------------------
// Video Gen
// ---------------------------------------------------------------------------

export type VideoType =
  | "explainer"
  | "promotional"
  | "tutorial"
  | "social_clip"
  | "presentation"
  | "avatar";

export interface GeneratedVideo {
  id: string;
  user_id: string;
  prompt: string;
  video_type: VideoType;
  video_url: string | null;
  duration_seconds: number | null;
  status: string;
  created_at: string;
}

export interface VideoGenerateRequest {
  prompt: string;
  video_type?: VideoType;
  duration_seconds?: number;
}

export interface VideoClipsRequest {
  transcription_id: string;
  max_clips?: number;
}

export interface VideoAvatarRequest {
  text: string;
  avatar_style?: string;
}

export interface VideoFromSourceRequest {
  source_id: string;
  source_type: "transcription" | "document";
  video_type?: VideoType;
}

// ---------------------------------------------------------------------------
// AI Chatbot Builder
// ---------------------------------------------------------------------------

export interface Chatbot {
  id: string;
  user_id: string;
  name: string;
  system_prompt: string;
  model_provider: string;
  knowledge_ids: string[];
  is_published: boolean;
  embed_token: string | null;
  channels: ChatbotChannel[];
  created_at: string;
  updated_at: string;
}

export interface ChatbotChannel {
  type: string;
  config: Record<string, unknown>;
}

export interface ChatbotCreateRequest {
  name: string;
  system_prompt?: string;
  model_provider?: string;
  knowledge_ids?: string[];
}

export interface ChatbotUpdateRequest {
  name?: string;
  system_prompt?: string;
  model_provider?: string;
  knowledge_ids?: string[];
}

export interface ChatbotAnalytics {
  chatbot_id: string;
  total_conversations: number;
  total_messages: number;
  avg_messages_per_session: number;
  top_topics: string[];
}

export interface ChatMessage {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  sources: Array<{ content: string; document: string; score: number }>;
}

// ---------------------------------------------------------------------------
// Marketplace
// ---------------------------------------------------------------------------

export type ListingCategory =
  | "template"
  | "workflow"
  | "agent"
  | "prompt"
  | "pipeline"
  | "chatbot"
  | "dataset"
  | "integration";

export interface MarketplaceListing {
  id: string;
  author_id: string;
  title: string;
  description: string;
  category: ListingCategory;
  price: number;
  is_free: boolean;
  rating: number;
  install_count: number;
  is_published: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface MarketplaceReview {
  id: string;
  user_id: string;
  listing_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface ListingCreateRequest {
  title: string;
  description: string;
  category: ListingCategory;
  price?: number;
  tags?: string[];
  content_data?: Record<string, unknown>;
}

export interface ListingUpdateRequest {
  title?: string;
  description?: string;
  price?: number;
  tags?: string[];
}

export interface ReviewCreateRequest {
  rating: number;
  comment?: string;
}

// ---------------------------------------------------------------------------
// Data Analyst
// ---------------------------------------------------------------------------

export interface Dataset {
  id: string;
  user_id: string;
  name: string;
  filename: string;
  row_count: number;
  column_count: number;
  columns: string[];
  preview: Record<string, unknown>[];
  created_at: string;
}

export interface DataAnalysis {
  id: string;
  dataset_id: string;
  analysis_type: string;
  result: Record<string, unknown>;
  created_at: string;
}

export interface DataAskRequest {
  question: string;
}

export interface DataAskResponse {
  question: string;
  sql_query: string;
  result: Record<string, unknown>;
  explanation: string;
}

export interface DataReportResponse {
  dataset_id: string;
  report: string;
  statistics: Record<string, unknown>;
  visualizations: string[];
}

// ---------------------------------------------------------------------------
// PDF Processor
// ---------------------------------------------------------------------------

export interface PdfResult {
  id: string;
  filename: string;
  page_count: number;
  text: string;
  tables: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Social Publisher
// ---------------------------------------------------------------------------

export interface SocialAccount {
  id: string;
  platform: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface SocialPost {
  id: string;
  user_id: string;
  content: string;
  platforms: string[];
  status: "draft" | "scheduled" | "published" | "failed";
  scheduled_at: string | null;
  published_at: string | null;
  created_at: string;
}

export interface SocialPostCreateRequest {
  content: string;
  platforms: string[];
  scheduled_at?: string;
}

export interface SocialPostAnalytics {
  post_id: string;
  impressions: number;
  engagements: number;
  clicks: number;
  platform_breakdown: Record<string, Record<string, number>>;
}

// ---------------------------------------------------------------------------
// AI Forms
// ---------------------------------------------------------------------------

export interface Form {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  fields: FormField[];
  is_published: boolean;
  share_token: string | null;
  status: "draft" | "published" | "closed";
  created_at: string;
  updated_at: string;
}

export interface FormField {
  name: string;
  label: string;
  type: string;
  required: boolean;
  options?: string[];
}

export interface FormCreateRequest {
  title: string;
  description?: string;
  fields: FormField[];
}

export interface FormUpdateRequest {
  title?: string;
  description?: string;
  fields?: FormField[];
}

export interface FormResponse {
  id: string;
  form_id: string;
  answers: Record<string, unknown>;
  score: number | null;
  created_at: string;
}

export interface FormGenerateRequest {
  prompt: string;
  field_count?: number;
}

// ---------------------------------------------------------------------------
// Code Sandbox
// ---------------------------------------------------------------------------

export interface Sandbox {
  id: string;
  user_id: string;
  name: string;
  language: string;
  cells: SandboxCell[];
  created_at: string;
  updated_at: string;
}

export interface SandboxCell {
  id: string;
  source: string;
  output: string | null;
  status: "idle" | "running" | "success" | "error";
  order: number;
}

export interface SandboxCreateRequest {
  name: string;
  language?: string;
}

export interface CodeGenerateRequest {
  prompt: string;
  language?: string;
}

export interface CodeGenerateResponse {
  code: string;
  language: string;
  explanation: string;
}

export interface CodeExplainRequest {
  code: string;
  language?: string;
}

export interface CodeDebugRequest {
  code: string;
  error: string;
  language?: string;
}

// ---------------------------------------------------------------------------
// Presentation Gen
// ---------------------------------------------------------------------------

export interface Presentation {
  id: string;
  user_id: string;
  title: string;
  template: string;
  slides: PresentationSlide[];
  created_at: string;
  updated_at: string;
}

export interface PresentationSlide {
  position: number;
  title: string;
  content: string;
  notes: string | null;
  layout: string;
}

export interface PresentationCreateRequest {
  topic: string;
  template?: string;
  slide_count?: number;
  language?: string;
}

export interface PresentationFromTranscriptRequest {
  transcription_id: string;
  template?: string;
  slide_count?: number;
}

export interface PresentationExportRequest {
  format: "html" | "markdown" | "pdf";
}

export interface PresentationTemplate {
  id: string;
  name: string;
  description: string;
  preview_url: string | null;
}

// ---------------------------------------------------------------------------
// Audio Studio
// ---------------------------------------------------------------------------

export interface AudioResult {
  id: string;
  filename: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  format: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Client Options
// ---------------------------------------------------------------------------

export interface SaaSIAClientOptions {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
}
