"""
Sentiment analysis service.

Uses AI to analyze sentiment and emotions in text.
Supports RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest) for fast
overall sentiment, with LLM fallback for segment analysis and emotions.
"""

import json
import re
from typing import Optional
from uuid import UUID

import structlog

try:
    from transformers import pipeline as hf_pipeline
    _sentiment_pipeline = None
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = structlog.get_logger()


class SentimentService:
    """Service for sentiment and emotion analysis."""

    @staticmethod
    async def analyze_text(text: str) -> dict:
        """
        Analyze sentiment of text using AI.

        Returns overall sentiment, segment-level analysis, and emotion summary.
        """
        # Split into segments (sentences or paragraphs)
        segments = SentimentService._split_into_segments(text)

        if not segments:
            return {
                "overall_sentiment": "neutral",
                "overall_score": 0.0,
                "segments": [],
                "emotion_summary": {},
                "positive_percent": 0.0,
                "negative_percent": 0.0,
                "neutral_percent": 0.0,
            }

        try:
            from app.ai_assistant.service import AIAssistantService

            # Batch analyze segments
            segments_text = "\n".join(f"[{i}] {s}" for i, s in enumerate(segments))

            prompt = f"""Analyze the sentiment of each numbered segment below. For each segment, provide:
- sentiment: "positive", "negative", or "neutral"
- score: a float from -1.0 (very negative) to 1.0 (very positive)
- emotions: list of detected emotions (joy, anger, sadness, fear, surprise, disgust, trust, anticipation)

Respond with a JSON array where each element has: segment_index, sentiment, score, emotions.

Text segments:
{segments_text[:8000]}

Respond ONLY with the JSON array."""

            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="sentiment_analysis",
                provider_name="gemini",
                module="sentiment",
            )

            response_text = result.get("processed_text", "[]")

            # Parse AI response
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start >= 0 and end > start:
                analysis = json.loads(response_text[start:end])
            else:
                analysis = []

            # Track AI cost
            try:
                from app.modules.cost_tracker.tracker import track_ai_usage
                await track_ai_usage(
                    user_id=None,
                    provider="gemini",
                    model="gemini-2.5-flash",
                    module="sentiment",
                    action="analyze_text",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=0,
                    success=True,
                )
            except Exception:
                pass  # Cost tracking should never break main flow

        except Exception as e:
            logger.warning("sentiment_ai_failed", error=str(e))
            # Fallback: simple keyword-based analysis
            analysis = [SentimentService._keyword_sentiment(s, i) for i, s in enumerate(segments)]

        # Build response
        analyzed_segments = []
        for i, seg_text in enumerate(segments):
            seg_data = next((a for a in analysis if a.get("segment_index") == i), None)
            if seg_data is None and i < len(analysis):
                seg_data = analysis[i] if isinstance(analysis, list) and i < len(analysis) else None

            if seg_data:
                analyzed_segments.append({
                    "text": seg_text,
                    "sentiment": seg_data.get("sentiment", "neutral"),
                    "score": float(seg_data.get("score", 0.0)),
                    "emotions": seg_data.get("emotions", []),
                })
            else:
                analyzed_segments.append({
                    "text": seg_text,
                    "sentiment": "neutral",
                    "score": 0.0,
                    "emotions": [],
                })

        # Compute overall metrics
        total = len(analyzed_segments)
        positive = sum(1 for s in analyzed_segments if s["sentiment"] == "positive")
        negative = sum(1 for s in analyzed_segments if s["sentiment"] == "negative")
        neutral = total - positive - negative

        avg_score = sum(s["score"] for s in analyzed_segments) / total if total > 0 else 0.0

        # Emotion summary
        emotion_counts: dict[str, int] = {}
        for seg in analyzed_segments:
            for emotion in seg.get("emotions", []):
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        overall = "positive" if avg_score > 0.1 else ("negative" if avg_score < -0.1 else "neutral")
        sentiment_method = "llm"

        # Try RoBERTa for a fast, high-quality overall sentiment override
        if HAS_TRANSFORMERS:
            try:
                roberta_result = SentimentService._analyze_with_roberta(text)
                overall = roberta_result["sentiment"]
                avg_score = roberta_result["score"]
                sentiment_method = "roberta"
                logger.info(
                    "sentiment_roberta_used",
                    sentiment=overall,
                    confidence=roberta_result["confidence"],
                )
            except Exception as e:
                logger.warning("sentiment_roberta_failed", error=str(e))
                # Fall through to LLM-computed overall sentiment
        else:
            logger.info("sentiment_method_llm", reason="transformers_not_available")

        return {
            "overall_sentiment": overall,
            "overall_score": round(avg_score, 3),
            "segments": analyzed_segments,
            "emotion_summary": emotion_counts,
            "positive_percent": round(positive / total * 100, 1) if total > 0 else 0.0,
            "negative_percent": round(negative / total * 100, 1) if total > 0 else 0.0,
            "neutral_percent": round(neutral / total * 100, 1) if total > 0 else 0.0,
            "sentiment_method": sentiment_method,
        }

    @staticmethod
    def _analyze_with_roberta(text: str) -> dict:
        """
        Fast sentiment analysis using cardiffnlp/twitter-roberta-base-sentiment-latest.

        ~100ms per call vs ~5s for LLM. Only provides overall sentiment
        (no segment-level analysis or emotions).
        """
        global _sentiment_pipeline
        if _sentiment_pipeline is None:
            _sentiment_pipeline = hf_pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            )
        # Model max token length is ~512 tokens; truncate input text to 512 chars
        # as a safe approximation.
        truncated = text[:512]
        results = _sentiment_pipeline(truncated)
        result = results[0]

        label_map = {
            "LABEL_0": "negative",
            "LABEL_1": "neutral",
            "LABEL_2": "positive",
            # Some model revisions use text labels directly
            "negative": "negative",
            "neutral": "neutral",
            "positive": "positive",
        }
        raw_label = result.get("label", "LABEL_1")
        sentiment = label_map.get(raw_label, "neutral")
        confidence = round(result.get("score", 0.0), 4)

        # Map sentiment to a score on [-1, 1]
        score_map = {"positive": confidence, "negative": -confidence, "neutral": 0.0}

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "label": raw_label,
            "score": round(score_map.get(sentiment, 0.0), 4),
            "method": "roberta",
        }

    @staticmethod
    def _split_into_segments(text: str) -> list[str]:
        """Split text into meaningful segments."""
        # Split by sentences or paragraphs
        segments = re.split(r'(?<=[.!?])\s+|\n\n+', text.strip())
        # Filter empty and very short segments
        return [s.strip() for s in segments if len(s.strip()) > 10]

    @staticmethod
    def _keyword_sentiment(text: str, index: int) -> dict:
        """Simple keyword-based sentiment fallback."""
        text_lower = text.lower()
        positive_words = {"good", "great", "excellent", "happy", "love", "amazing", "wonderful", "fantastic", "bien", "super", "genial", "parfait", "excellent", "merci"}
        negative_words = {"bad", "terrible", "awful", "hate", "horrible", "poor", "wrong", "mal", "mauvais", "nul", "probleme", "erreur", "echec"}

        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        if pos_count > neg_count:
            return {"segment_index": index, "sentiment": "positive", "score": min(pos_count * 0.3, 1.0), "emotions": ["joy"]}
        elif neg_count > pos_count:
            return {"segment_index": index, "sentiment": "negative", "score": max(-neg_count * 0.3, -1.0), "emotions": ["sadness"]}
        return {"segment_index": index, "sentiment": "neutral", "score": 0.0, "emotions": []}
