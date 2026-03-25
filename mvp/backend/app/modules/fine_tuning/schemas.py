"""
Fine-Tuning Studio schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TrainingSample(BaseModel):
    """A single training sample."""
    instruction: str = Field(default="")
    input: str = Field(default="")
    output: str = Field(default="")
    system: Optional[str] = None


class DatasetCreate(BaseModel):
    """Create a training dataset."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    dataset_type: str = Field(default="instruction", description="instruction, conversation, completion, classification")
    samples: list[TrainingSample] = Field(default_factory=list)
    validation_split: float = Field(default=0.1, ge=0.0, le=0.5)


class DatasetFromSourceRequest(BaseModel):
    """Create dataset from existing platform data."""
    name: str = Field(..., min_length=1, max_length=200)
    source_type: str = Field(..., description="transcriptions, conversations, documents, knowledge_qa")
    dataset_type: str = Field(default="instruction")
    max_samples: int = Field(default=100, ge=1, le=10000)
    filters: dict = Field(default_factory=dict, description="Optional filters (language, status, date_from)")


class DatasetRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    dataset_type: str
    source_type: str
    sample_count: int
    validation_split: float
    quality_score: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddSamplesRequest(BaseModel):
    """Add samples to an existing dataset."""
    samples: list[TrainingSample] = Field(..., min_length=1, max_length=500)


class FineTuneCreate(BaseModel):
    """Create a fine-tuning job."""
    name: str = Field(..., min_length=1, max_length=200)
    dataset_id: str = Field(...)
    base_model: str = Field(default="llama-3.3-8b", description="llama-3.3-8b, llama-3.3-70b, mistral-7b, gemma-2b, gpt-4o-mini")
    provider: str = Field(default="together", description="together, openai, replicate")
    hyperparams: dict = Field(default_factory=dict, description="epochs, learning_rate, batch_size, lora_rank, lora_alpha")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Custom Model",
                "dataset_id": "...",
                "base_model": "llama-3.3-8b",
                "hyperparams": {"epochs": 3, "learning_rate": 2e-5, "batch_size": 4, "lora_rank": 16},
            }
        }


class FineTuneJobRead(BaseModel):
    id: UUID
    user_id: UUID
    dataset_id: UUID
    name: str
    base_model: str
    provider: str
    status: str
    hyperparams_json: str
    metrics_json: str
    result_model_id: Optional[str]
    error: Optional[str]
    epochs_completed: int
    total_epochs: int
    estimated_cost_usd: float
    actual_cost_usd: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EvalRequest(BaseModel):
    """Evaluate a fine-tuned model."""
    test_prompts: list[dict] = Field(..., min_length=1, max_length=50, description="[{prompt, expected_output}]")
    eval_type: str = Field(default="benchmark", description="benchmark, comparison, custom")


class EvalRead(BaseModel):
    id: UUID
    job_id: UUID
    eval_type: str
    metrics_json: str
    base_model_score: Optional[float]
    tuned_model_score: Optional[float]
    improvement_pct: Optional[float]
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableModel(BaseModel):
    """A base model available for fine-tuning."""
    id: str
    name: str
    provider: str
    parameters: str
    cost_per_1k_tokens: float
    supports_lora: bool
    max_context: int
