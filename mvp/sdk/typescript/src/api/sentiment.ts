import { BaseAPI } from "./base";
import {
  SentimentAnalyzeRequest,
  SentimentResult,
  SentimentTranscriptionRequest,
} from "../types";

/**
 * Sentiment API — text sentiment analysis using RoBERTa + LLM fallback.
 */
export class SentimentAPI extends BaseAPI {
  /** Analyze text sentiment and emotions. */
  async analyze(data: SentimentAnalyzeRequest): Promise<SentimentResult> {
    return this._post<SentimentResult>("/api/sentiment/analyze", data);
  }

  /** Analyze sentiment of a transcription. */
  async analyzeTranscription(data: SentimentTranscriptionRequest): Promise<SentimentResult> {
    return this._post<SentimentResult>("/api/sentiment/transcription", data);
  }
}
