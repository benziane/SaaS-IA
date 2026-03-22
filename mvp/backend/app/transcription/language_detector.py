"""
Language Detection Service - Grade S++
Intelligent language detection for YouTube videos
"""

import re
from typing import Optional, Dict
import structlog

logger = structlog.get_logger()


class LanguageDetector:
    """Intelligent language detection for transcription"""
    
    # Language keywords mapping
    LANGUAGE_KEYWORDS = {
        'fr': [
            'français', 'france', 'french', 'fr', 'francais',
            'allah', 'coran', 'islam', 'musulman', 'prière',
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de',
            'est', 'sont', 'être', 'avoir', 'faire'
        ],
        'en': [
            'english', 'en', 'us', 'uk', 'america', 'british',
            'the', 'is', 'are', 'was', 'were', 'be', 'have',
            'do', 'does', 'did', 'will', 'would', 'can', 'could'
        ],
        'ar': [
            'arabic', 'ar', 'عربي', 'العربية', 'مسلم', 'إسلام',
            'قرآن', 'صلاة', 'الله', 'محمد'
        ],
        'es': [
            'español', 'spanish', 'es', 'españa', 'mexico',
            'el', 'la', 'los', 'las', 'un', 'una', 'es', 'son'
        ],
        'de': [
            'deutsch', 'german', 'de', 'deutschland',
            'der', 'die', 'das', 'ein', 'eine', 'ist', 'sind'
        ],
        'it': [
            'italiano', 'italian', 'it', 'italia',
            'il', 'la', 'i', 'le', 'un', 'una', 'è', 'sono'
        ],
        'pt': [
            'português', 'portuguese', 'pt', 'brasil', 'portugal',
            'o', 'a', 'os', 'as', 'um', 'uma', 'é', 'são'
        ],
        'ru': [
            'russian', 'ru', 'россия', 'русский',
            'это', 'быть', 'не', 'на', 'я', 'он'
        ],
        'zh': [
            'chinese', 'zh', 'china', '中文', '中国',
            '的', '是', '在', '有', '我', '他'
        ],
        'ja': [
            'japanese', 'ja', 'japan', '日本', '日本語',
            'の', 'に', 'は', 'を', 'た', 'が'
        ],
        'hi': [
            'hindi', 'hi', 'india', 'हिंदी', 'भारत',
            'है', 'हैं', 'का', 'की', 'के', 'में'
        ],
    }
    
    # AssemblyAI supported languages
    ASSEMBLYAI_LANGUAGES = {
        'fr': 'fr',
        'en': 'en',
        'es': 'es',
        'de': 'de',
        'it': 'it',
        'pt': 'pt',
        'nl': 'nl',
        'hi': 'hi',
        'ja': 'ja',
        'zh': 'zh',
        'fi': 'fi',
        'ko': 'ko',
        'pl': 'pl',
        'ru': 'ru',
        'tr': 'tr',
        'uk': 'uk',
        'vi': 'vi',
    }
    
    @staticmethod
    def detect_language_from_metadata(metadata: Dict) -> Optional[str]:
        """
        Detect language from YouTube video metadata
        
        Args:
            metadata: YouTube video metadata (title, uploader, etc.)
        
        Returns:
            ISO 639-1 language code or None
        """
        try:
            # Combine all text fields
            text_to_analyze = " ".join([
                str(metadata.get('title', '')),
                str(metadata.get('uploader', '')),
                str(metadata.get('description', '')),
            ]).lower()
            
            logger.info(
                "language_detection_start",
                text_sample=text_to_analyze[:200]
            )
            
            # Score each language
            language_scores = {}
            
            for lang_code, keywords in LanguageDetector.LANGUAGE_KEYWORDS.items():
                score = 0
                for keyword in keywords:
                    # Count occurrences (case insensitive)
                    count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text_to_analyze))
                    score += count
                
                if score > 0:
                    language_scores[lang_code] = score
            
            # Get language with highest score
            if language_scores:
                detected_lang = max(language_scores, key=language_scores.get)
                confidence = language_scores[detected_lang]
                
                logger.info(
                    "language_detected",
                    language=detected_lang,
                    confidence=confidence,
                    all_scores=language_scores
                )
                
                # Only return if supported by AssemblyAI
                if detected_lang in LanguageDetector.ASSEMBLYAI_LANGUAGES:
                    return detected_lang
                else:
                    logger.warning(
                        "language_not_supported",
                        detected_language=detected_lang,
                        supported_languages=list(LanguageDetector.ASSEMBLYAI_LANGUAGES.keys())
                    )
                    return None
            
            logger.info("no_language_detected", text_analyzed=text_to_analyze[:100])
            return None
            
        except Exception as e:
            logger.error("language_detection_error", error=str(e))
            return None
    
    @staticmethod
    def get_language_name(lang_code: str) -> str:
        """Get human-readable language name"""
        language_names = {
            'fr': 'French',
            'en': 'English',
            'es': 'Spanish',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'hi': 'Hindi',
            'ja': 'Japanese',
            'zh': 'Chinese',
            'fi': 'Finnish',
            'ko': 'Korean',
            'pl': 'Polish',
            'ru': 'Russian',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'vi': 'Vietnamese',
            'ar': 'Arabic',
        }
        return language_names.get(lang_code, lang_code.upper())
    
    @staticmethod
    def is_supported_by_assemblyai(lang_code: str) -> bool:
        """Check if language is supported by AssemblyAI"""
        return lang_code in LanguageDetector.ASSEMBLYAI_LANGUAGES


__all__ = ["LanguageDetector"]

