import asyncio
import json
import os
import sys
from datetime import datetime

# Add Backend to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database.session import SessionLocal
from app.services.evaluation_service import EvaluationService

async def main():
    method = sys.argv[1] if len(sys.argv) > 1 else "heuristic"
    print(f"Running evaluation with method: {method}")
    
    db = SessionLocal()
    from app.core.config import settings
    print(f"DEBUG: settings.LLM_PROVIDER={settings.LLM_PROVIDER}")
    print(f"DEBUG: settings.GEMINI_API_KEY={'PRESENT' if settings.GEMINI_API_KEY else 'MISSING'}")
    print(f"DEBUG: settings.OPENAI_API_KEY={'PRESENT' if settings.OPENAI_API_KEY else 'MISSING'}")
    
    try:
        service = EvaluationService(db)
        results = await service.run_full_evaluation(method)
        
        print("\n" + "="*80)
        print(f" GROBSAI - SYSTEM EVALUATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print(f"{'Feature Category':<30} | {'Compl.':<6} | {'Acc.':<6} | {'Prec.':<6} | {'Lat.':<6}")
        print("-" * 80)
        for f in results["features_data"]:
            print(f"{f['name']:<30} | {f['completeness']:>5}% | {f['accuracy']:>5}% | {f['precision']:>5}% | {f['efficiency']:>4}ms")
        print("-" * 80)
        print(f" OVERALL ACCURACY: {results['overall_accuracy']:>5}% | AVG LATENCY: {results['average_latency']:>5}ms")
        print("="*80 + "\n")
        
        # Output core analysis as requested in prompt
        print("CORE ANALYSIS (FOUR KEY FEATURES):")
        for core in results["core_analysis"]:
            print(f"- {core['name']}: Accuracy {core['accuracy']}%, Latency {core['latency']}ms")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
