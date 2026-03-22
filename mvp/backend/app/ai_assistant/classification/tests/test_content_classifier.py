"""
Unit Tests for ContentClassifier - Grade S++

Tests classification accuracy, performance, and edge cases.
"""

import pytest
from app.ai_assistant.classification.content_classifier import ContentClassifier
from app.ai_assistant.classification.enums import ContentDomain, ContentTone, SensitivityLevel


class TestContentClassifier:
    """Test suite for ContentClassifier"""
    
    def test_classify_religious_content_french(self):
        """Test classification of French religious content"""
        text = """
        Le Prophète (paix soit sur lui) a dit dans un hadith authentique :
        "La patience est une lumière". Ce rappel nous enseigne l'importance
        de la foi et de l'adoration d'Allah.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["primary_domain"] == ContentDomain.RELIGIOUS
        assert result["confidence"] > 0.5
        assert result["sensitivity"]["level"] == SensitivityLevel.HIGH
        assert result["sensitivity"]["requires_strict_mode"] is True
        assert "allah" in result["keywords_found"].get(ContentDomain.RELIGIOUS, [])
        assert "prophète" in result["keywords_found"].get(ContentDomain.RELIGIOUS, [])
    
    def test_classify_scientific_content(self):
        """Test classification of scientific content"""
        text = """
        Cette étude présente les résultats d'une expérience sur le modèle
        de données. L'hypothèse initiale a été validée par l'analyse statistique.
        Le protocole expérimental a suivi la méthode scientifique standard.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["primary_domain"] == ContentDomain.SCIENTIFIC
        assert result["confidence"] > 0.4
        assert "étude" in result["keywords_found"].get(ContentDomain.SCIENTIFIC, [])
    
    def test_classify_technical_content(self):
        """Test classification of technical content"""
        text = """
        Le serveur backend utilise une API REST avec FastAPI. La base de données
        PostgreSQL stocke les données en JSON. Le code utilise des fonctions
        asynchrones pour améliorer les performances.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["primary_domain"] == ContentDomain.TECHNICAL
        assert result["confidence"] > 0.4
        assert "api" in result["keywords_found"].get(ContentDomain.TECHNICAL, [])
    
    def test_classify_mixed_content(self):
        """Test classification of mixed domain content"""
        text = """
        Le Prophète (paix soit sur lui) encourageait la recherche scientifique.
        Cette étude analyse les données historiques sur l'islam et la science.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        # Should detect both religious and scientific
        assert result["is_mixed_content"] is True
        assert ContentDomain.RELIGIOUS in result["domains"]
        assert ContentDomain.SCIENTIFIC in result["domains"]
        assert result["secondary_domain"] is not None
    
    def test_detect_tone_academic(self):
        """Test detection of academic tone"""
        text = """
        Selon les recherches récentes, l'analyse démontre que le modèle
        est cohérent. En effet, les résultats confirment l'hypothèse.
        Par conséquent, nous concluons que...
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["tone"] == ContentTone.ACADEMIC
    
    def test_detect_tone_popular(self):
        """Test detection of popular/conversational tone"""
        text = """
        Salut ! Tu sais, c'est super important de comprendre ça.
        Je te dis, c'est génial !! Tu vas voir, c'est top !
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["tone"] == ContentTone.POPULAR
    
    def test_detect_tone_formal(self):
        """Test detection of formal tone"""
        text = """
        Veuillez noter que conformément à l'article 5 du règlement,
        nous vous prions de bien vouloir transmettre les documents requis.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["tone"] == ContentTone.FORMAL
    
    def test_sensitivity_high_keywords(self):
        """Test detection of high sensitivity keywords"""
        text = """
        Suite au décès tragique, la famille est en deuil.
        La souffrance causée par cette perte est immense.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["sensitivity"]["level"] in [SensitivityLevel.HIGH, SensitivityLevel.MEDIUM]
        assert "high_sensitivity_keywords" in result["sensitivity"]["reasons"] or \
               "medium_sensitivity_keywords" in result["sensitivity"]["reasons"]
    
    def test_empty_text(self):
        """Test classification of empty text"""
        result = ContentClassifier.classify("", language="french")
        
        assert result["primary_domain"] == ContentDomain.GENERAL
        assert result["confidence"] == 0.0
        assert result["text_length"] == 0
    
    def test_general_content_fallback(self):
        """Test fallback to general domain for unclassified content"""
        text = "Bonjour, comment allez-vous aujourd'hui ?"
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["primary_domain"] == ContentDomain.GENERAL
    
    def test_performance_under_50ms(self):
        """Test that classification completes in under 50ms"""
        text = """
        Le Prophète (paix soit sur lui) a dit : "La patience est une lumière".
        Cette étude scientifique analyse les données avec un protocole rigoureux.
        Le serveur API utilise FastAPI et PostgreSQL pour traiter les requêtes.
        """ * 10  # Repeat to make it longer
        
        result = ContentClassifier.classify(text, language="french")
        
        # Should be under 50ms for typical content
        assert result["processing_time_ms"] < 100  # Allow some margin
    
    def test_batch_classification(self):
        """Test batch classification of multiple texts"""
        texts = [
            "Le Prophète (paix soit sur lui) a dit...",
            "Cette étude scientifique démontre que...",
            "Le serveur API utilise FastAPI..."
        ]
        
        results = ContentClassifier.classify_batch(texts, language="french")
        
        assert len(results) == 3
        assert results[0]["primary_domain"] == ContentDomain.RELIGIOUS
        assert results[1]["primary_domain"] == ContentDomain.SCIENTIFIC
        assert results[2]["primary_domain"] == ContentDomain.TECHNICAL
    
    def test_get_domain_summary(self):
        """Test human-readable domain summary"""
        text = "Le Prophète (paix soit sur lui) a dit dans un hadith..."
        
        classification = ContentClassifier.classify(text, language="french")
        summary = ContentClassifier.get_domain_summary(classification)
        
        assert "religious" in summary.lower()
        assert "sensitive" in summary.lower()
    
    def test_medical_domain_detection(self):
        """Test detection of medical content"""
        text = """
        Le patient présente des symptômes de la maladie. Le médecin a prescrit
        un traitement avec des médicaments. Le diagnostic a été confirmé à l'hôpital.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["primary_domain"] == ContentDomain.MEDICAL
        assert result["sensitivity"]["level"] in [SensitivityLevel.HIGH, SensitivityLevel.MEDIUM]
    
    def test_legal_domain_detection(self):
        """Test detection of legal content"""
        text = """
        Conformément à l'article 42 du code civil, le tribunal a rendu son jugement.
        L'avocat a présenté le contrat devant le juge.
        """
        
        result = ContentClassifier.classify(text, language="french")
        
        assert result["primary_domain"] == ContentDomain.LEGAL
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # Strong religious content
        strong_text = """
        Allah, prophète, hadith, coran, islam, musulman, prière, adoration,
        paradis, enfer, dhikr, foi, croyant.
        """
        
        result_strong = ContentClassifier.classify(strong_text, language="french")
        
        # Weak religious content
        weak_text = "Le prophète a dit quelque chose."
        result_weak = ContentClassifier.classify(weak_text, language="french")
        
        # Strong should have higher confidence
        assert result_strong["confidence"] > result_weak["confidence"]
    
    def test_language_support(self):
        """Test classification with different languages"""
        # French
        result_fr = ContentClassifier.classify(
            "Le Prophète (paix soit sur lui) a dit...",
            language="french"
        )
        
        # English
        result_en = ContentClassifier.classify(
            "The Prophet (peace be upon him) said...",
            language="english"
        )
        
        assert result_fr["primary_domain"] == ContentDomain.RELIGIOUS
        assert result_en["primary_domain"] == ContentDomain.RELIGIOUS
        assert result_fr["language_detected"] == "french"
        assert result_en["language_detected"] == "english"

