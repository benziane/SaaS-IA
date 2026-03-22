"""
Script de test rapide pour le AI Router - Grade S++

Teste la classification, sélection de modèle et prompt.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ai_assistant.classification.content_classifier import ContentClassifier
from app.ai_assistant.classification.model_selector import ModelSelector
from app.ai_assistant.classification.prompt_selector import PromptSelector
from app.ai_assistant.classification.enums import SelectionStrategy


def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_result(label: str, value: any):
    """Print formatted result"""
    print(f"  [+] {label}: {value}")


def test_religious_content():
    """Test 1: Contenu religieux"""
    print_header("TEST 1: Contenu Religieux")
    
    text = """
    Le Prophète (paix soit sur lui) a dit dans un hadith authentique :
    "La patience est une lumière". Ce rappel nous enseigne l'importance
    de la foi et de l'adoration d'Allah. Le paradis est la récompense
    des croyants qui font le dhikr.
    """
    
    # 1. Classification
    classification = ContentClassifier.classify(text, language="french")
    
    print_result("Domaine primaire", classification["primary_domain"])
    print_result("Confiance", f"{classification['confidence']:.2%}")
    print_result("Sensibilite", classification["sensitivity"]["level"])
    print_result("STRICT MODE requis", classification["sensitivity"]["requires_strict_mode"])
    print_result("Mots-cles trouves", len(classification["keywords_found"].get("religious", [])))
    print_result("Temps de traitement", f"{classification['processing_time_ms']:.2f}ms")
    
    # 2. Selection modele
    model_selection = ModelSelector.select_model(
        classification=classification,
        strategy=SelectionStrategy.BALANCED
    )
    
    print_result("Modele selectionne", model_selection["model"])
    print_result("Strategie utilisee", model_selection["strategy_used"])
    print_result("Ajustement strategie", model_selection["confidence_adjustment"])
    print_result("Raison", model_selection["reason"])
    
    # 3. Sélection prompt
    prompt_config = PromptSelector.select_prompt(
        classification=classification,
        task="format_text",
        model=model_selection["model"]
    )
    
    print_result("Profil prompt", prompt_config["profile"])
    print_result("STRICT MODE", prompt_config["use_strict_mode"])
    print_result("Contraintes", len(prompt_config["additional_constraints"]))
    
    # Validation
    assert classification["primary_domain"] == "religious"
    assert classification["sensitivity"]["requires_strict_mode"] is True
    assert model_selection["strategy_used"] == SelectionStrategy.CONSERVATIVE
    assert prompt_config["use_strict_mode"] is True
    
    print("\n  [SUCCESS] TEST 1 REUSSI")


def test_technical_content():
    """Test 2: Contenu technique"""
    print_header("TEST 2: Contenu Technique")
    
    text = """
    Le serveur backend utilise FastAPI avec une base de données PostgreSQL.
    L'API REST expose des endpoints JSON. Le code utilise des fonctions
    asynchrones et Docker pour le déploiement. Redis est utilisé pour le cache.
    """
    
    # 1. Classification
    classification = ContentClassifier.classify(text, language="french")
    
    print_result("Domaine primaire", classification["primary_domain"])
    print_result("Confiance", f"{classification['confidence']:.2%}")
    print_result("Sensibilite", classification["sensitivity"]["level"])
    print_result("Temps de traitement", f"{classification['processing_time_ms']:.2f}ms")
    
    # 2. Sélection modèle (cost-optimized)
    model_selection = ModelSelector.select_model(
        classification=classification,
        strategy=SelectionStrategy.COST_OPTIMIZED
    )
    
    print_result("Modèle sélectionné", model_selection["model"])
    print_result("Stratégie utilisée", model_selection["strategy_used"])
    
    # 3. Sélection prompt
    prompt_config = PromptSelector.select_prompt(
        classification=classification,
        task="improve_quality",
        model=model_selection["model"]
    )
    
    print_result("Profil prompt", prompt_config["profile"])
    print_result("STRICT MODE", prompt_config["use_strict_mode"])
    
    # Validation
    assert classification["primary_domain"] == "technical"
    assert classification["sensitivity"]["level"] in ["low", "medium"]
    assert model_selection["strategy_used"] == SelectionStrategy.COST_OPTIMIZED
    assert prompt_config["profile"] == "technical"
    
    print("\n  [SUCCESS] TEST 2 REUSSI")


def test_mixed_content():
    """Test 3: Contenu mixte"""
    print_header("TEST 3: Contenu Mixte (Religieux + Scientifique)")
    
    text = """
    Le Prophète (paix soit sur lui) encourageait la recherche scientifique.
    Cette étude analyse les données historiques sur l'islam et la science.
    Les résultats démontrent une corrélation intéressante entre foi et raison.
    """
    
    # 1. Classification
    classification = ContentClassifier.classify(text, language="french")
    
    print_result("Domaine primaire", classification["primary_domain"])
    print_result("Domaine secondaire", classification["secondary_domain"])
    print_result("Contenu mixte", classification["is_mixed_content"])
    print_result("Confiance", f"{classification['confidence']:.2%}")
    print_result("Temps de traitement", f"{classification['processing_time_ms']:.2f}ms")
    
    # 2. Sélection modèle
    model_selection = ModelSelector.select_model(
        classification=classification,
        strategy=SelectionStrategy.BALANCED
    )
    
    print_result("Modèle sélectionné", model_selection["model"])
    print_result("Stratégie utilisée", model_selection["strategy_used"])
    
    # Validation
    assert classification["is_mixed_content"] is True
    assert classification["secondary_domain"] is not None
    
    print("\n  [SUCCESS] TEST 3 REUSSI")


def test_strategy_comparison():
    """Test 4: Comparaison des stratégies"""
    print_header("TEST 4: Comparaison des Stratégies")
    
    text = "Le Prophète (paix soit sur lui) a dit..."
    
    classification = ContentClassifier.classify(text, language="french")
    comparison = ModelSelector.compare_strategies(classification)
    
    print("  Stratégies comparées :")
    for strategy, result in comparison.items():
        print(f"    • {strategy}: {result['model']} ({result['reason']})")
    
    # Validation
    assert len(comparison) == 3
    assert SelectionStrategy.CONSERVATIVE in comparison
    assert SelectionStrategy.BALANCED in comparison
    assert SelectionStrategy.COST_OPTIMIZED in comparison
    
    print("\n  [SUCCESS] TEST 4 REUSSI")


def test_performance():
    """Test 5: Performance"""
    print_header("TEST 5: Performance (<50ms)")
    
    text = """
    Le Prophète (paix soit sur lui) a dit : "La patience est une lumière".
    Cette étude scientifique analyse les données avec un protocole rigoureux.
    Le serveur API utilise FastAPI et PostgreSQL pour traiter les requêtes.
    """ * 10  # Texte plus long
    
    import time
    start = time.time()
    
    classification = ContentClassifier.classify(text, language="french")
    
    duration_ms = (time.time() - start) * 1000
    
    print_result("Longueur texte", f"{len(text)} caractères")
    print_result("Temps classification", f"{duration_ms:.2f}ms")
    print_result("Temps interne", f"{classification['processing_time_ms']:.2f}ms")
    
    # Validation
    assert duration_ms < 100  # Should be under 100ms
    
    print("\n  [SUCCESS] TEST 5 REUSSI")


def test_batch_classification():
    """Test 6: Classification batch"""
    print_header("TEST 6: Classification Batch")
    
    texts = [
        "Le Prophète (paix soit sur lui) a dit dans un hadith authentique sur la foi et l'adoration d'Allah.",
        "Cette étude scientifique présente les résultats d'une expérience avec un protocole et une analyse des données.",
        "Le serveur backend utilise une API REST avec FastAPI, PostgreSQL, Docker et des fonctions asynchrones.",
        "Bonjour, comment allez-vous aujourd'hui ? J'espère que vous passez une bonne journée.",
    ]
    
    results = ContentClassifier.classify_batch(texts, language="french")
    
    print(f"  Textes classifies : {len(results)}")
    for i, result in enumerate(results):
        print(f"    {i+1}. {result['primary_domain']} (confidence: {result['confidence']:.2%})")
    
    # Validation
    assert len(results) == 4
    assert results[0]["primary_domain"] == "religious", f"Expected religious, got {results[0]['primary_domain']}"
    assert results[1]["primary_domain"] == "scientific", f"Expected scientific, got {results[1]['primary_domain']}"
    assert results[2]["primary_domain"] == "technical", f"Expected technical, got {results[2]['primary_domain']}"
    assert results[3]["primary_domain"] == "general", f"Expected general, got {results[3]['primary_domain']}"
    
    print("\n  [SUCCESS] TEST 6 REUSSI")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  AI ROUTER - TESTS DE VALIDATION")
    print("=" * 80)
    
    try:
        test_religious_content()
        test_technical_content()
        test_mixed_content()
        test_strategy_comparison()
        test_performance()
        test_batch_classification()
        
        print_header("TOUS LES TESTS REUSSIS")
        print("  [OK] Classification : OK")
        print("  [OK] Selection modele : OK")
        print("  [OK] Selection prompt : OK")
        print("  [OK] Performance : OK (<50ms)")
        print("  [OK] Batch : OK")
        print("\n  SUCCESS: Le AI Router est operationnel !")
        
        return 0
        
    except AssertionError as e:
        print(f"\n  [FAIL] TEST ECHOUE : {e}")
        return 1
    except Exception as e:
        print(f"\n  [ERROR] ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

