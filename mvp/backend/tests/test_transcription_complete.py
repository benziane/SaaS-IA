"""
Test Backend-Only : Transcription Complète
Grade S++ - Test automatique de bout en bout

Ce script teste la transcription complète d'une vidéo YouTube
avec amélioration AI, en arrière-plan, sans interface.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.transcription import YouTubeService, AssemblyAIService
from app.transcription.language_detector import LanguageDetector
from app.ai_assistant.service import AIAssistantService
import structlog

logger = structlog.get_logger()


class TranscriptionTester:
    """Test complet de transcription avec AI"""
    
    def __init__(self, video_url: str):
        self.video_url = video_url
        self.start_time = datetime.utcnow()
        self.results = {}
    
    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def print_step(self, step_num: int, title: str, status: str = "⏳"):
        """Print step info"""
        print(f"{status} STEP {step_num}: {title}")
    
    async def run_test(self):
        """Run complete transcription test"""
        self.print_header("🧪 TEST TRANSCRIPTION COMPLETE - BACKEND ONLY")
        
        print(f"📹 Video URL: {self.video_url}")
        print(f"⏰ Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # STEP 1: Validate YouTube URL
            self.print_step(1, "YOUTUBE URL VALIDATION")
            video_id = YouTubeService.extract_video_id(self.video_url)
            if not video_id:
                raise ValueError(f"Invalid YouTube URL: {self.video_url}")
            print(f"   ✅ Valid! Video ID: {video_id}")
            self.results["video_id"] = video_id
            
            # STEP 2: Download Audio
            self.print_step(2, "YOUTUBE AUDIO DOWNLOAD")
            audio_file, metadata = await asyncio.to_thread(
                YouTubeService.download_audio,
                self.video_url
            )
            file_size = os.path.getsize(audio_file)
            print(f"   ✅ Downloaded! Size: {round(file_size / 1024 / 1024, 2)} MB")
            print(f"   📊 Title: {metadata.get('title', 'N/A')}")
            print(f"   ⏱️  Duration: {metadata.get('duration', 'N/A')}s")
            self.results["audio_file"] = audio_file
            self.results["metadata"] = metadata
            
            # STEP 3: Detect Language
            self.print_step(3, "LANGUAGE DETECTION")
            detected_language = LanguageDetector.detect_language_from_metadata(metadata)
            if detected_language:
                language_name = LanguageDetector.get_language_name(detected_language)
                print(f"   ✅ Detected: {detected_language} ({language_name})")
            else:
                print(f"   ⚠️  No language detected, using auto-detect")
            self.results["detected_language"] = detected_language
            
            # STEP 4: Transcribe with AssemblyAI
            self.print_step(4, "ASSEMBLYAI TRANSCRIPTION")
            transcription_result = await asyncio.to_thread(
                AssemblyAIService.transcribe_audio,
                audio_file,
                detected_language
            )
            raw_text = transcription_result["text"]
            confidence = transcription_result.get("confidence", 0.0)
            print(f"   ✅ Transcribed! Confidence: {round(confidence * 100, 1)}%")
            print(f"   📝 Length: {len(raw_text)} chars, {len(raw_text.split())} words")
            self.results["raw_text"] = raw_text
            self.results["confidence"] = confidence
            
            # STEP 5: Select FREE AI Provider
            self.print_step(5, "AI PROVIDER SELECTION")
            best_provider = AIAssistantService.get_best_provider(
                prefer_free=True,
                exclude=["claude"]  # ❌ NEVER use Claude (paid)
            )
            print(f"   ✅ Selected: {best_provider.upper()} (FREE 🆓)")
            self.results["ai_provider"] = best_provider
            
            # STEP 6: Improve with AI (Primary Provider)
            self.print_step(6, "AI QUALITY IMPROVEMENT (Primary)")
            improved_result = await AIAssistantService.process_text(
                text=raw_text,
                task="improve_quality",
                provider_name=best_provider,
                language=detected_language
            )
            improved_text = improved_result["processed_text"]
            print(f"   ✅ Improved! Provider: {improved_result['provider_used']}")
            print(f"   📝 Length: {len(improved_text)} chars, {len(improved_text.split())} words")
            self.results["improved_text"] = improved_text
            
            # STEP 7: Restructure with Gemini (intelligent content restructuring)
            self.print_step(7, "AI CONTENT RESTRUCTURING WITH GEMINI")
            try:
                gemini_result = await AIAssistantService.process_text(
                    text=raw_text,
                    task="format_text",
                    provider_name="gemini",
                    language=detected_language
                )
                gemini_text = gemini_result["processed_text"]
                growth_ratio = (len(gemini_text) / len(raw_text) - 1) * 100
                print(f"   ✅ Restructured! Provider: Gemini (FREE 🆓)")
                print(f"   📝 Length: {len(gemini_text)} chars, {len(gemini_text.split())} words")
                print(f"   📊 Growth: {growth_ratio:+.1f}% (target: max +50%)")
                self.results["gemini_text"] = gemini_text
            except Exception as e:
                print(f"   ⚠️  Gemini restructuring failed: {str(e)}")
                self.results["gemini_text"] = None
            
            # STEP 8: Restructure with Groq (intelligent content restructuring)
            self.print_step(8, "AI CONTENT RESTRUCTURING WITH GROQ")
            try:
                groq_result = await AIAssistantService.process_text(
                    text=raw_text,
                    task="format_text",
                    provider_name="groq",
                    language=detected_language
                )
                groq_text = groq_result["processed_text"]
                growth_ratio = (len(groq_text) / len(raw_text) - 1) * 100
                print(f"   ✅ Restructured! Provider: Groq (FREE 🆓)")
                print(f"   📝 Length: {len(groq_text)} chars, {len(groq_text.split())} words")
                print(f"   📊 Growth: {growth_ratio:+.1f}% (target: max +50%)")
                self.results["groq_text"] = groq_text
            except Exception as e:
                print(f"   ⚠️  Groq restructuring failed: {str(e)}")
                self.results["groq_text"] = None
            
            # STEP 9: Cleanup
            self.print_step(9, "CLEANUP TEMPORARY FILES")
            try:
                import shutil
                temp_dir = os.path.dirname(audio_file)
                shutil.rmtree(temp_dir)
                print(f"   ✅ Cleaned: {temp_dir}")
            except Exception as e:
                print(f"   ⚠️  Cleanup failed: {str(e)}")
            
            # FINAL RESULTS
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            self.print_header("✅ TEST COMPLETE - RESULTS")
            
            print(f"⏱️  Total Duration: {duration:.2f}s")
            print(f"🎯 Confidence: {round(confidence * 100, 1)}%")
            print(f"🤖 AI Provider: {best_provider.upper()} (FREE 🆓)")
            print(f"📊 Language: {detected_language or 'auto'}")
            print()
            
            print("📝 RAW TEXT (AssemblyAI):")
            print("-" * 80)
            print(raw_text[:800] + "..." if len(raw_text) > 800 else raw_text)
            print()
            
            print("✨ IMPROVED TEXT (AI - Primary):")
            print("-" * 80)
            print(improved_text[:800] + "..." if len(improved_text) > 800 else improved_text)
            print()
            
            # Show Gemini result
            if self.results.get("gemini_text"):
                print("✨ GEMINI RESTRUCTURED CONTENT (FREE 🆓):")
                print("-" * 80)
                gemini_text = self.results["gemini_text"]
                print(gemini_text[:800] + "..." if len(gemini_text) > 800 else gemini_text)
                print()
            
            # Show Groq result
            if self.results.get("groq_text"):
                print("⚡ GROQ RESTRUCTURED CONTENT (FREE 🆓):")
                print("-" * 80)
                groq_text = self.results["groq_text"]
                print(groq_text[:800] + "..." if len(groq_text) > 800 else groq_text)
                print()
            
            # Show full texts if small enough
            if len(raw_text) <= 2000:
                print("📄 FULL RAW TEXT:")
                print("=" * 80)
                print(raw_text)
                print()
            
            if len(improved_text) <= 2000:
                print("📄 FULL IMPROVED TEXT (Primary):")
                print("=" * 80)
                print(improved_text)
                print()
            
            if self.results.get("gemini_text") and len(self.results["gemini_text"]) <= 2000:
                print("📄 FULL GEMINI TEXT:")
                print("=" * 80)
                print(self.results["gemini_text"])
                print()
            
            if self.results.get("groq_text") and len(self.results["groq_text"]) <= 2000:
                print("📄 FULL GROQ TEXT:")
                print("=" * 80)
                print(self.results["groq_text"])
                print()
            
            # Comparison
            improvement_ratio = len(improved_text) / len(raw_text) if raw_text else 1.0
            print("📊 COMPARISON:")
            print(f"   Raw:      {len(raw_text)} chars, {len(raw_text.split())} words")
            print(f"   Improved: {len(improved_text)} chars, {len(improved_text.split())} words")
            print(f"   Ratio:    {improvement_ratio:.2f}x")
            print(f"   AI Cost:  FREE 🆓 (using {best_provider})")
            
            if self.results.get("gemini_text"):
                gemini_text = self.results["gemini_text"]
                gemini_ratio = len(gemini_text) / len(raw_text) if raw_text else 1.0
                print(f"\n   Gemini:   {len(gemini_text)} chars, {len(gemini_text.split())} words")
                print(f"   Ratio:    {gemini_ratio:.2f}x")
                print(f"   Cost:     FREE 🆓")
            
            if self.results.get("groq_text"):
                groq_text = self.results["groq_text"]
                groq_ratio = len(groq_text) / len(raw_text) if raw_text else 1.0
                print(f"\n   Groq:     {len(groq_text)} chars, {len(groq_text.split())} words")
                print(f"   Ratio:    {groq_ratio:.2f}x")
                print(f"   Cost:     FREE 🆓")
            print()
            
            self.print_header("🎉 SUCCESS!")
            return True
            
        except Exception as e:
            self.print_header("❌ TEST FAILED")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main test function"""
    # Video de test (déjà utilisée dans les tests précédents)
    video_url = "https://youtu.be/C49V1SArjtY"
    
    tester = TranscriptionTester(video_url)
    success = await tester.run_test()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

