/**
 * Transcription Schemas - Grade S++
 * Zod validation schemas for transcription
 */

import { z } from 'zod';

/* ========================================================================
   VALIDATION RULES
   ======================================================================== */

const YOUTUBE_URL_REGEX =
  /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{11}(&.*)?$/;

/* ========================================================================
   TRANSCRIPTION CREATE SCHEMA
   ======================================================================== */

export const transcriptionCreateSchema = z.object({
  video_url: z
    .string()
    .min(1, 'YouTube URL is required')
    .url('Invalid URL format')
    .regex(YOUTUBE_URL_REGEX, 'Invalid YouTube URL. Please provide a valid YouTube video URL')
    .trim(),
});

export type TranscriptionCreateSchema = z.infer<typeof transcriptionCreateSchema>;

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  transcriptionCreateSchema,
};

