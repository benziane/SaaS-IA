"""
Test AI Router Integration in Transcription Module

Validates that the AI Router is correctly integrated and working.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import structlog
from app.ai_assistant.service import AIAssistantService
from app.ai_assistant.classification.model_selector import SelectionStrategy
from app.database import get_session_context

logger = structlog.get_logger()


async def test_router_integration():
    """Test AI Router integration with transcription-like content"""
    
    print("\n" + "=" * 80)
    print("  TEST AI ROUTER INTEGRATION - TRANSCRIPTION MODULE")
    print("=" * 80 + "\n")
    
    # Test cases simulating different types of YouTube transcriptions
    test_cases = [
        {
            "name": "Religious Content (French)",
            "text": """
            Assalamu alaikum mes frères et sœurs. Aujourd'hui on va parler de l'importance 
            de la prière dans notre vie quotidienne. Le Prophète paix soit sur lui a dit 
            que la prière est le pilier de l'islam. C'est notre connexion directe avec Allah.
            Quand on prie, on se rapproche du Créateur. C'est un moment de paix et de sérénité.
            """,
            "language": "french",
            "expected_domain": "religious",
            "expected_model": "groq",  # Conservative for religious
            "strategy": SelectionStrategy.CONSERVATIVE
        },
        {
            "name": "Technical Tutorial (French)",
            "text": """
            Bonjour à tous, dans cette vidéo on va voir comment déployer une API FastAPI 
            avec Docker. D'abord, on crée un Dockerfile, ensuite on configure docker-compose,
            et enfin on lance le conteneur. C'est très simple, vous allez voir.
            On va aussi parler de Nginx comme reverse proxy et de PostgreSQL pour la base de données.
            """,
            "language": "french",
            "expected_domain": "technical",
            "expected_model": "gemini-flash",  # Cost optimized for technical
            "strategy": SelectionStrategy.COST_OPTIMIZED
        },
        {
            "name": "General Vlog (French)",
            "text": """
            Salut tout le monde ! Aujourd'hui je vous emmène avec moi pour une journée shopping.
            On va aller dans plusieurs magasins, je vais vous montrer mes coups de cœur.
            J'espère que la vidéo va vous plaire, n'oubliez pas de vous abonner et de liker !
            """,
            "language": "french",
            "expected_domain": "general",
            "expected_model": "gemini-flash",  # Cost optimized for general
            "strategy": SelectionStrategy.COST_OPTIMIZED
        },
        {
            "name": "Scientific Content (French)",
            "text": """
            Cette étude scientifique démontre que le réchauffement climatique a un impact 
            significatif sur les écosystèmes marins. Les données collectées sur une période 
            de 10 ans montrent une augmentation de la température de l'eau de 2 degrés Celsius.
            Le protocole expérimental utilisé garantit la fiabilité des résultats obtenus.
            """,
            "language": "french",
            "expected_domain": "scientific",
            "expected_model": "gemini-pro",  # Conservative for scientific
            "strategy": SelectionStrategy.CONSERVATIVE
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"  TEST {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'=' * 80}\n")
        
        try:
            async with get_session_context() as session:
                # Use AI Router
                result = await AIAssistantService.process_text_smart(
                    db=session,
                    text=test_case["text"],
                    task="improve_quality",
                    language=test_case["language"],
                    metadata={
                        "source": "youtube_transcription_test",
                        "test_case": test_case["name"]
                    },
                    strategy=test_case["strategy"]
                )
                
                # Extract classification and model selection
                classification = result.get("classification", {})
                model_selection = result.get("model_selection", {})
                prompt_config = result.get("prompt_config", {})
                
                # Check results
                domain_match = classification.get("primary_domain") == test_case["expected_domain"]
                model_match = model_selection.get("model") == test_case["expected_model"]
                
                print(f"📊 CLASSIFICATION:")
                print(f"   Domain: {classification.get('primary_domain')} (expected: {test_case['expected_domain']})")
                print(f"   Confidence: {classification.get('confidence')}")
                print(f"   Sensitivity: {classification.get('sensitivity', {}).get('level')}")
                print(f"   Tone: {classification.get('tone')}")
                print(f"   Mixed: {classification.get('is_mixed_content')}")
                
                print(f"\n🤖 MODEL SELECTION:")
                print(f"   Model: {model_selection.get('model')} (expected: {test_case['expected_model']})")
                print(f"   Strategy: {model_selection.get('strategy_used')}")
                print(f"   Fallback: {model_selection.get('fallback_used')}")
                print(f"   Reason: {model_selection.get('reason')}")
                
                print(f"\n📝 PROMPT CONFIG:")
                print(f"   Profile: {prompt_config.get('profile')}")
                print(f"   Strict Mode: {prompt_config.get('strict_mode')}")
                
                print(f"\n⏱️  PERFORMANCE:")
                print(f"   Total Time: {result.get('total_processing_time_ms'):.2f} ms")
                print(f"   Classification: {classification.get('processing_time_ms'):.2f} ms")
                
                print(f"\n✅ VALIDATION:")
                print(f"   Domain Match: {'✅ YES' if domain_match else '❌ NO'}")
                print(f"   Model Match: {'✅ YES' if model_match else '⚠️  DIFFERENT (not a failure)'}")
                
                results.append({
                    "test_case": test_case["name"],
                    "domain_match": domain_match,
                    "model_match": model_match,
                    "classification": classification,
                    "model_selection": model_selection
                })
                
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "test_case": test_case["name"],
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("  📊 SUMMARY")
    print("=" * 80 + "\n")
    
    total_tests = len(test_cases)
    successful_tests = len([r for r in results if "error" not in r])
    domain_matches = len([r for r in results if r.get("domain_match")])
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}/{total_tests}")
    print(f"Domain Matches: {domain_matches}/{total_tests}")
    
    if successful_tests == total_tests and domain_matches >= total_tests * 0.75:
        print("\n✅ INTEGRATION TEST PASSED")
        print("   AI Router is correctly integrated in transcription module!")
        return True
    else:
        print("\n⚠️  INTEGRATION TEST PARTIAL SUCCESS")
        print("   AI Router is working but some classifications may need tuning.")
        return False


async def main():
    try:
        success = await test_router_integration()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

