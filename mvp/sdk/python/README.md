# saas-ia-client -- Official SaaS-IA Python SDK

Async Python SDK for the SaaS-IA modular AI platform. Covers 19 module APIs with clean `async/await` usage.

## Installation

```bash
pip install saas-ia-client
# or from source
pip install -e mvp/sdk/python
```

## Quick Start

```python
import asyncio
from saas_ia import SaaSIAClient

async def main():
    async with SaaSIAClient(base_url="http://localhost:8004") as client:
        # Authenticate
        await client.login("user@example.com", "password")

        # List transcriptions
        result = await client.transcription.list(limit=10)
        print(f"Total: {result['total']}")

asyncio.run(main())
```

## Usage Examples

### Transcription

```python
# Create a transcription job
job = await client.transcription.create(
    "https://youtube.com/watch?v=dQw4w9WgXcQ",
    language="en",
)

# Smart transcribe with provider routing
result = await client.transcription.smart_transcribe(
    "https://youtube.com/watch?v=...",
    enable_diarization=True,
)

# Auto-generate chapters
chapters = await client.transcription.chapters(job["id"])

# Export as SRT subtitles
srt = await client.transcription.export(job["id"], "srt")

# Batch transcription
batch = await client.transcription.batch([
    "https://youtube.com/watch?v=...",
    "https://youtube.com/watch?v=...",
])
```

### Knowledge Base

```python
# Upload a document
with open("report.txt", "rb") as f:
    doc = await client.knowledge.upload(f, "report.txt")

# Hybrid search (auto-detects best mode)
results = await client.knowledge.search("machine learning", limit=5)

# RAG question answering
answer = await client.knowledge.ask(
    "What are the key takeaways?",
    limit=5,
)
print(answer["answer"])
print(f"Provider: {answer['provider']}")
```

### Conversation

```python
# Create a conversation linked to a transcription
conv = await client.conversation.create(
    transcription_id="uuid-here",
)

# Chat
reply = await client.conversation.send_message(
    conv["id"],
    "Summarize the key points",
)
print(reply["content"])
```

### Content Studio

```python
# Create project and generate content
project = await client.content_studio.create_project(
    "Q1 Report",
    source_text="Our Q1 results show...",
)

pieces = await client.content_studio.generate(
    project["id"],
    ["blog_post", "social_media", "newsletter"],
    tone="professional",
)
```

### Pipelines

```python
# Create and execute a pipeline
pipeline = await client.pipelines.create(
    "Content Pipeline",
    steps=[
        {"type": "transcribe", "config": {"language": "en"}, "order": 0},
        {"type": "summarize", "config": {"style": "bullets"}, "order": 1},
    ],
)

execution = await client.pipelines.execute(
    pipeline["id"],
    input_data={"source_url": "https://youtube.com/watch?v=..."},
)
```

### Agents

```python
# Run an autonomous agent
run = await client.agents.run(
    "Research competitors and create a summary report",
    max_steps=10,
)

# ReAct agent
react = await client.agents.react(
    "Find all documents about AI safety and summarize them",
    max_iterations=5,
)
```

### AI Chatbot Builder

```python
# Create and publish a chatbot
bot = await client.chatbot.create(
    "Support Bot",
    system_prompt="You are a helpful support assistant.",
    knowledge_ids=["doc-uuid-1", "doc-uuid-2"],
)

result = await client.chatbot.publish(bot["id"])
embed_token = result["embed_token"]
```

### Data Analyst

```python
# Upload and analyze a CSV
with open("sales.csv", "rb") as f:
    dataset = await client.data_analyst.upload_dataset(f, "sales.csv")

# Natural language query
answer = await client.data_analyst.ask(
    dataset["id"],
    "What is the average revenue by region?",
)
print(answer["explanation"])
print(f"SQL: {answer['sql_query']}")
```

### Compare

```python
# Compare AI providers
comparison = await client.compare.run(
    "Explain quantum computing in simple terms",
    providers=["gemini", "claude", "groq"],
)

for resp in comparison["responses"]:
    print(f"{resp['provider']}: {resp['latency_ms']}ms")

# Vote for the best
await client.compare.vote(comparison["id"], "claude")
```

### Marketplace

```python
# Browse and install
listings = await client.marketplace.browse(category="template", limit=20)
await client.marketplace.install(listings[0]["id"])
```

## API Reference

| Property | Module | Description |
|----------|--------|-------------|
| `client.transcription` | `TranscriptionAPI` | YouTube/audio/video transcription |
| `client.conversation` | `ConversationAPI` | Contextual AI chat |
| `client.knowledge` | `KnowledgeAPI` | Document upload + hybrid search + RAG |
| `client.content_studio` | `ContentStudioAPI` | Multi-format content generation |
| `client.pipelines` | `PipelineAPI` | Sequential AI operation chaining |
| `client.agents` | `AgentAPI` | Autonomous AI agents |
| `client.compare` | `CompareAPI` | Multi-provider comparison |
| `client.sentiment` | `SentimentAPI` | Text sentiment analysis |
| `client.image_gen` | `ImageGenAPI` | AI image generation |
| `client.video_gen` | `VideoGenAPI` | Text-to-video generation |
| `client.chatbot` | `ChatbotAPI` | RAG chatbot builder |
| `client.marketplace` | `MarketplaceAPI` | Community marketplace |
| `client.data_analyst` | `DataAnalystAPI` | CSV/JSON data analysis |
| `client.pdf` | `PDFAPI` | PDF text/table extraction |
| `client.social_publisher` | `SocialPublisherAPI` | Social media publishing |
| `client.forms` | `FormsAPI` | AI-powered forms |
| `client.code_sandbox` | `CodeSandboxAPI` | Secure code execution |
| `client.presentation_gen` | `PresentationGenAPI` | AI slide generation |
| `client.audio_studio` | `AudioStudioAPI` | Audio editing |

## Error Handling

```python
from saas_ia import SaaSIAClient, SaaSIAError

async with SaaSIAClient() as client:
    try:
        await client.transcription.get("nonexistent-id")
    except SaaSIAError as e:
        print(f"API error {e.status}: {e.detail}")
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | `http://localhost:8004` | API base URL |
| `api_key` | `str` | `None` | API key for Public API v1 |
| `timeout` | `float` | `30.0` | Request timeout in seconds |

## License

Proprietary
