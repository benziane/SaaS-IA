"""Unified Search schemas."""
from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    type: str
    title: str
    content: str
    score: float
    url: str


class UnifiedSearchResponse(BaseModel):
    query: str
    total: int
    results: list[dict]
    facets: dict
