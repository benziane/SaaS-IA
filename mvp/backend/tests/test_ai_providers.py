"""
Test AI Providers - Validate API Keys
Grade S++ - Quick validation script

This script tests all AI providers (Gemini, Groq, Claude) to ensure
API keys are correctly configured and working.
"""

import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_assistant.providers import GeminiProvider, GroqProvider, ClaudeProvider
import structlog

logger = structlog.get_logger()


async def test_provider(provider_class, provider_name: str):
    """Test a single AI provider."""
    print(f"\n{'='*80}")
    print(f"  Testing {provider_name.upper()}")
    print(f"{'='*80}\n")
    
    try:
        # Initialize provider
        print(f"[1/3] Initializing {provider_name}...")
        provider = provider_class()
        print(f"   ✅ Provider initialized")
        print(f"   📊 Model: {provider.model_name}")
        print(f"   💰 Cost: {'FREE 🆓' if provider.is_free else 'PAID 💰'}")
        
        # Test simple prompt
        print(f"\n[2/3] Testing simple prompt...")
        test_prompt = "Say 'Hello' in one word only."
        
        response_chunks = []
        async for chunk in provider.stream_chat(test_prompt):
            response_chunks.append(chunk)
        
        response = "".join(response_chunks).strip()
        print(f"   ✅ Response received: '{response[:50]}...'")
        print(f"   📝 Length: {len(response)} chars")
        
        # Test with longer prompt
        print(f"\n[3/3] Testing longer prompt...")
        test_prompt_long = "Write a short sentence about AI in French."
        
        response_chunks = []
        async for chunk in provider.stream_chat(test_prompt_long):
            response_chunks.append(chunk)
        
        response = "".join(response_chunks).strip()
        print(f"   ✅ Response received: '{response[:100]}...'")
        print(f"   📝 Length: {len(response)} chars")
        
        print(f"\n{'='*80}")
        print(f"  ✅ {provider_name.upper()} - ALL TESTS PASSED")
        print(f"{'='*80}\n")
        return True
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"  ❌ {provider_name.upper()} - TEST FAILED")
        print(f"{'='*80}")
        print(f"\n❌ Error: {str(e)}")
        print(f"❌ Error Type: {type(e).__name__}\n")
        return False


async def main():
    """Main test function."""
    print("\n" + "="*80)
    print("  🧪 AI PROVIDERS VALIDATION TEST")
    print("="*80)
    print("\nThis script validates that all AI provider API keys are working correctly.\n")
    
    results = {}
    
    # Test Gemini
    results["gemini"] = await test_provider(GeminiProvider, "Gemini")
    
    # Test Groq
    results["groq"] = await test_provider(GroqProvider, "Groq")
    
    # Test Claude (optional, may not be configured)
    try:
        results["claude"] = await test_provider(ClaudeProvider, "Claude")
    except ValueError as e:
        if "not configured" in str(e):
            print(f"\n{'='*80}")
            print(f"  ⚠️  CLAUDE - SKIPPED (Not configured)")
            print(f"{'='*80}\n")
            results["claude"] = None
        else:
            results["claude"] = False
    
    # Summary
    print("\n" + "="*80)
    print("  📊 TEST SUMMARY")
    print("="*80 + "\n")
    
    for provider, status in results.items():
        if status is True:
            print(f"  ✅ {provider.upper()}: WORKING")
        elif status is False:
            print(f"  ❌ {provider.upper()}: FAILED")
        elif status is None:
            print(f"  ⚠️  {provider.upper()}: NOT CONFIGURED")
    
    print()
    
    # Check if at least one provider is working
    working_providers = [p for p, s in results.items() if s is True]
    
    if len(working_providers) >= 2:
        print("="*80)
        print("  🎉 SUCCESS - At least 2 providers are working!")
        print("="*80)
        print(f"\n✅ Working providers: {', '.join([p.upper() for p in working_providers])}\n")
        sys.exit(0)
    elif len(working_providers) == 1:
        print("="*80)
        print("  ⚠️  WARNING - Only 1 provider is working")
        print("="*80)
        print(f"\n⚠️  Working provider: {working_providers[0].upper()}")
        print("⚠️  Consider adding more API keys for redundancy\n")
        sys.exit(0)
    else:
        print("="*80)
        print("  ❌ FAILURE - No providers are working!")
        print("="*80)
        print("\n❌ Please check your API keys in .env file\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

