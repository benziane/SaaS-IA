"""
Service for post-processing and correcting transcriptions
"""
import re
import asyncio
from typing import Dict, List, Optional
import language_tool_python
from deepmultilingualpunctuation import PunctuationModel

from app.core.config import settings


class TranscriptPostProcessor:
    """Service for correcting and formatting transcriptions"""

    def __init__(self):
        """Initialize post-processor with language tools"""
        self._punctuation_model = None
        self._language_tools = {}  # Cache for language-specific tools

    def _load_punctuation_model(self):
        """Load punctuation restoration model (lazy loading)"""
        if self._punctuation_model is None:
            print("Loading punctuation model...")
            self._punctuation_model = PunctuationModel()
        return self._punctuation_model

    def _get_language_tool(self, language: str):
        """
        Get or create LanguageTool instance for specific language

        Args:
            language: Language code (en, fr, ar, etc.)

        Returns:
            LanguageTool instance
        """
        if not settings.LANGUAGE_TOOL_ENABLED:
            return None

        if language not in self._language_tools:
            try:
                # Map language codes to LanguageTool codes
                lang_map = {
                    "en": "en-US",
                    "fr": "fr",
                    "ar": "ar",
                    "es": "es",
                    "de": "de-DE",
                    "it": "it",
                    "pt": "pt-PT",
                }
                lang_code = lang_map.get(language, language)
                self._language_tools[language] = language_tool_python.LanguageTool(lang_code)
            except Exception as e:
                print(f"Failed to load LanguageTool for {language}: {e}")
                return None

        return self._language_tools[language]

    async def restore_punctuation(self, text: str) -> str:
        """
        Restore punctuation using deep learning model

        Args:
            text: Text without proper punctuation

        Returns:
            Text with restored punctuation
        """
        try:
            model = self._load_punctuation_model()
            loop = asyncio.get_event_loop()

            # Split text into chunks if too long
            max_length = 500
            if len(text) < max_length:
                result = await loop.run_in_executor(
                    None,
                    model.restore_punctuation,
                    text
                )
                return result
            else:
                # Process in chunks
                chunks = self._split_into_chunks(text, max_length)
                results = []

                for chunk in chunks:
                    result = await loop.run_in_executor(
                        None,
                        model.restore_punctuation,
                        chunk
                    )
                    results.append(result)

                return " ".join(results)

        except Exception as e:
            print(f"Punctuation restoration failed: {e}")
            return text

    def _split_into_chunks(self, text: str, max_length: int) -> List[str]:
        """
        Split text into chunks at sentence boundaries

        Args:
            text: Text to split
            max_length: Maximum chunk length

        Returns:
            List of text chunks
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > max_length and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    async def correct_grammar(self, text: str, language: str = "en") -> Dict:
        """
        Correct grammar and spelling errors

        Args:
            text: Text to correct
            language: Language code

        Returns:
            Dictionary with corrected text and corrections made
        """
        tool = self._get_language_tool(language)

        if not tool:
            return {
                "text": text,
                "corrections": [],
                "error_count": 0
            }

        try:
            loop = asyncio.get_event_loop()

            # Get matches
            matches = await loop.run_in_executor(
                None,
                tool.check,
                text
            )

            # Apply corrections
            corrected_text = await loop.run_in_executor(
                None,
                language_tool_python.utils.correct,
                text,
                matches
            )

            # Extract correction details
            corrections = [
                {
                    "original": text[m.offset:m.offset + m.errorLength],
                    "correction": m.replacements[0] if m.replacements else "",
                    "message": m.message,
                    "type": m.ruleId,
                }
                for m in matches
            ]

            return {
                "text": corrected_text,
                "corrections": corrections,
                "error_count": len(corrections)
            }

        except Exception as e:
            print(f"Grammar correction failed: {e}")
            return {
                "text": text,
                "corrections": [],
                "error_count": 0
            }

    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace and formatting

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)

        # Add space after punctuation if missing
        text = re.sub(r'([.,!?;:])([A-Za-z])', r'\1 \2', text)

        # Capitalize first letter of sentences
        text = re.sub(
            r'(^|[.!?]\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            text
        )

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def remove_filler_words(self, text: str, language: str = "en") -> str:
        """
        Remove common filler words and verbal tics

        Args:
            text: Text to clean
            language: Language code

        Returns:
            Cleaned text
        """
        # Define filler words by language
        fillers = {
            "en": [
                r'\b(um|uh|er|ah|like|you know|I mean|basically|actually|literally)\b',
            ],
            "fr": [
                r'\b(euh|ben|genre|tu vois|en fait|donc|du coup|voilà)\b',
            ],
            "ar": [
                r'\b(يعني|طيب|أه)\b',
            ]
        }

        pattern = fillers.get(language, [])

        for p in pattern:
            text = re.sub(p, '', text, flags=re.IGNORECASE)

        # Clean up resulting multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def format_paragraphs(self, text: str, sentences_per_paragraph: int = 5) -> str:
        """
        Format text into paragraphs

        Args:
            text: Text to format
            sentences_per_paragraph: Number of sentences per paragraph

        Returns:
            Formatted text with paragraphs
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Group into paragraphs
        paragraphs = []
        for i in range(0, len(sentences), sentences_per_paragraph):
            paragraph = " ".join(sentences[i:i + sentences_per_paragraph])
            paragraphs.append(paragraph)

        return "\n\n".join(paragraphs)

    async def process(
        self,
        text: str,
        language: str = "en",
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Complete post-processing pipeline

        Args:
            text: Raw transcript text
            language: Language code
            options: Processing options (restore_punctuation, correct_grammar, etc.)

        Returns:
            Dictionary with processed text and metadata
        """
        options = options or {}

        # Default options
        restore_punctuation = options.get("restore_punctuation", True)
        correct_grammar = options.get("correct_grammar", True)
        remove_fillers = options.get("remove_filler_words", True)
        format_text = options.get("format_paragraphs", True)

        processing_steps = []
        current_text = text

        # Step 1: Normalize whitespace
        current_text = self.normalize_whitespace(current_text)
        processing_steps.append("normalize_whitespace")

        # Step 2: Remove filler words
        if remove_fillers:
            current_text = self.remove_filler_words(current_text, language)
            processing_steps.append("remove_filler_words")

        # Step 3: Restore punctuation
        if restore_punctuation:
            current_text = await self.restore_punctuation(current_text)
            processing_steps.append("restore_punctuation")

        # Step 4: Correct grammar
        correction_result = None
        if correct_grammar:
            correction_result = await self.correct_grammar(current_text, language)
            current_text = correction_result["text"]
            processing_steps.append("correct_grammar")

        # Step 5: Format paragraphs
        if format_text:
            current_text = self.format_paragraphs(current_text)
            processing_steps.append("format_paragraphs")

        return {
            "original_text": text,
            "processed_text": current_text,
            "language": language,
            "processing_steps": processing_steps,
            "corrections": correction_result["corrections"] if correction_result else [],
            "error_count": correction_result["error_count"] if correction_result else 0,
            "character_count": len(current_text),
            "word_count": len(current_text.split()),
        }

    def __del__(self):
        """Cleanup language tools"""
        for tool in self._language_tools.values():
            try:
                tool.close()
            except:
                pass
