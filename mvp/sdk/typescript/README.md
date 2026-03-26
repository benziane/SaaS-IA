# @saas-ia/sdk — Official SaaS-IA TypeScript SDK

TypeScript/JavaScript SDK for the SaaS-IA modular AI platform. Covers 19 module APIs with full type safety.

## Installation

```bash
npm install @saas-ia/sdk
# or
yarn add @saas-ia/sdk
```

## Quick Start

```typescript
import { SaaSIAClient } from "@saas-ia/sdk";

const client = new SaaSIAClient({
  baseUrl: "http://localhost:8004", // default
});

// Authenticate
await client.login("user@example.com", "password");

// Or use an API key for Public API v1
const publicClient = new SaaSIAClient({
  baseUrl: "http://localhost:8004",
  apiKey: "sk-your-api-key",
});
```

## Usage Examples

### Transcription

```typescript
// Transcribe a YouTube video
const job = await client.transcription.create({
  source_url: "https://youtube.com/watch?v=dQw4w9WgXcQ",
  language: "en",
});

// List transcriptions
const { items, total } = await client.transcription.list({ limit: 10 });

// Smart transcribe with automatic provider routing
const result = await client.transcription.smartTranscribe({
  source_url: "https://youtube.com/watch?v=...",
  enable_diarization: true,
});

// Auto-generate chapters
const { chapters } = await client.transcription.chapters(job.id);

// Export as SRT subtitles
const srt = await client.transcription.export(job.id, "srt");

// Batch transcribe
const batch = await client.transcription.batch([
  "https://youtube.com/watch?v=...",
  "https://youtube.com/watch?v=...",
]);
```

### Knowledge Base

```typescript
// Upload a document
const doc = await client.knowledge.upload(myFile);

// Hybrid search (auto-detects best mode)
const results = await client.knowledge.search({
  query: "machine learning best practices",
  limit: 5,
});

// RAG question answering
const answer = await client.knowledge.ask({
  question: "What are the key takeaways from the uploaded documents?",
});

// Check search modes availability
const status = await client.knowledge.searchStatus();
```

### Conversation

```typescript
// Start a conversation linked to a transcription
const conv = await client.conversation.create({
  transcription_id: "uuid-here",
});

// Send a message and get AI response
const reply = await client.conversation.sendMessage(conv.id, {
  content: "Summarize the key points discussed in this video",
});
```

### Content Studio

```typescript
// Create a project and generate content
const project = await client.contentStudio.createProject({
  title: "Q1 Report",
  source_text: "Our Q1 results show...",
});

const pieces = await client.contentStudio.generate(project.id, {
  formats: ["blog_post", "social_media", "newsletter"],
  tone: "professional",
});
```

### Pipelines

```typescript
// Create and execute a pipeline
const pipeline = await client.pipelines.create({
  name: "Content Pipeline",
  steps: [
    { type: "transcribe", config: { language: "en" }, order: 0 },
    { type: "summarize", config: { style: "bullets" }, order: 1 },
    { type: "translate", config: { target: "fr" }, order: 2 },
  ],
});

const execution = await client.pipelines.execute(pipeline.id, {
  input_data: { source_url: "https://youtube.com/watch?v=..." },
});
```

### Agents

```typescript
// Run an autonomous agent
const run = await client.agents.run({
  goal: "Research competitors and create a summary report",
  max_steps: 10,
});

// ReAct agent
const react = await client.agents.react({
  instruction: "Find all documents about AI safety and summarize them",
  max_iterations: 5,
});
```

### AI Chatbot Builder

```typescript
// Create and publish a chatbot
const bot = await client.chatbot.create({
  name: "Support Bot",
  system_prompt: "You are a helpful support assistant.",
  knowledge_ids: ["doc-uuid-1", "doc-uuid-2"],
});

const { embed_token } = await client.chatbot.publish(bot.id);
const embedCode = await client.chatbot.embedCode(bot.id);
```

### Marketplace

```typescript
// Browse listings
const listings = await client.marketplace.browse({
  category: "template",
  limit: 20,
});

// Install a listing
await client.marketplace.install(listings[0].id);
```

### Data Analyst

```typescript
// Upload and analyze a dataset
const dataset = await client.dataAnalyst.uploadDataset(csvFile);

// Ask questions in natural language
const answer = await client.dataAnalyst.ask(dataset.id, {
  question: "What is the average revenue by region?",
});

// Generate a comprehensive report
const report = await client.dataAnalyst.report(dataset.id);
```

### Compare

```typescript
// Compare AI providers
const comparison = await client.compare.run({
  prompt: "Explain quantum computing in simple terms",
  providers: ["gemini", "claude", "groq"],
});

// Vote for the best
await client.compare.vote(comparison.id, {
  winner_provider: "claude",
});
```

## API Reference

### `SaaSIAClient`

| Property | Type | Description |
|----------|------|-------------|
| `transcription` | `TranscriptionAPI` | YouTube/audio/video transcription |
| `conversation` | `ConversationAPI` | Contextual AI chat |
| `knowledge` | `KnowledgeAPI` | Document upload + hybrid search + RAG |
| `contentStudio` | `ContentStudioAPI` | Multi-format content generation |
| `pipelines` | `PipelineAPI` | Sequential AI operation chaining |
| `agents` | `AgentAPI` | Autonomous AI agents |
| `compare` | `CompareAPI` | Multi-provider comparison |
| `sentiment` | `SentimentAPI` | Text sentiment analysis |
| `imageGen` | `ImageGenAPI` | AI image generation |
| `videoGen` | `VideoGenAPI` | Text-to-video generation |
| `chatbot` | `ChatbotAPI` | RAG chatbot builder |
| `marketplace` | `MarketplaceAPI` | Community marketplace |
| `dataAnalyst` | `DataAnalystAPI` | CSV/JSON data analysis |
| `pdf` | `PDFAPI` | PDF text/table extraction |
| `socialPublisher` | `SocialPublisherAPI` | Social media publishing |
| `forms` | `FormsAPI` | AI-powered forms |
| `codeSandbox` | `CodeSandboxAPI` | Secure code execution |
| `presentationGen` | `PresentationGenAPI` | AI slide generation |
| `audioStudio` | `AudioStudioAPI` | Audio editing |

### Error Handling

```typescript
import { SaaSIAError } from "@saas-ia/sdk";

try {
  await client.transcription.get("nonexistent-id");
} catch (err) {
  if (err instanceof SaaSIAError) {
    console.error(`API error ${err.status}: ${err.detail}`);
  }
}
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `baseUrl` | `string` | `http://localhost:8004` | API base URL |
| `apiKey` | `string` | — | API key for Public API v1 |
| `timeout` | `number` | `30000` | Request timeout in ms |

## Building from source

```bash
npm install
npm run build
```

## License

Proprietary
