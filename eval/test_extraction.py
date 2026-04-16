import json
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent'))

from tools.extract_jobs import extract_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_FIXTURES = [
    {
        "name": "RevenueRat Careers Page",
        "url": "https://revenuecat.com/careers",
        "page_text": """
            RevenueRat is hiring!
            
            We are looking for passionate engineers to join our team.
            
            OPEN POSITIONS:
            
            Senior Backend Engineer
            Build scalable backend services using Java and Spring Boot. 
            Work on REST APIs, microservices, and cloud infrastructure.
            Location: San Francisco, CA
            
            Product Manager – Mobile
            Lead product strategy for our mobile applications.
            Experience with iOS/Android ecosystems required.
            Location: Remote
            
            DevOps Engineer
            Manage our Kubernetes infrastructure and CI/CD pipelines.
            Strong experience with AWS, Docker, and infrastructure-as-code.
            Location: New York, NY
        """,
        "expected_titles": [
            "Senior Backend Engineer",
            "Product Manager – Mobile",
            "DevOps Engineer"
        ]
    },
    {
        "name": "Anthropic Careers Page",
        "url": "https://anthropic.com/careers",
        "page_text": """
            Anthropic Careers
            
            Join our team building safe AI systems.
            
            CURRENT OPENINGS:
            
            AI Research Engineer
            Work on scaling laws and foundation model research.
            PhD or equivalent experience in ML/AI required.
            San Francisco, CA
            
            Machine Learning Infrastructure Engineer
            Build tools and systems for training large language models.
            Experience with distributed computing and GPU optimization.
            Remote position available
            
            Senior Policy Researcher
            Help shape governance and policy for advanced AI systems.
            Background in policy, law, or international relations.
            Washington, DC / Remote
        """,
        "expected_titles": [
            "AI Research Engineer",
            "Machine Learning Infrastructure Engineer",
            "Senior Policy Researcher"
        ]
    }
]


def run_evals() -> dict:
    """Run extraction evals on all fixtures and return results."""
    total_fixtures = len(TEST_FIXTURES)
    passed = 0
    failed = 0
    precisions = []
    recalls = []
    
    for fixture in TEST_FIXTURES:
        name = fixture["name"]
        url = fixture["url"]
        page_text = fixture["page_text"]
        expected_titles = fixture["expected_titles"]
        
        # Extract jobs
        try:
            extracted_jobs = extract_jobs(page_text, url)
        except Exception as e:
            logger.error(f"Fixture '{name}' failed to extract: {e}")
            failed += 1
            precisions.append(0.0)
            recalls.append(0.0)
            continue
        
        # Find matches (case-insensitive contains)
        extracted_titles = [job.get("title", "") for job in extracted_jobs]
        correct_count = 0
        
        for extracted_title in extracted_titles:
            for expected_title in expected_titles:
                if expected_title.lower() in extracted_title.lower():
                    correct_count += 1
                    break
        
        # Calculate precision and recall
        precision = correct_count / len(extracted_titles) if extracted_titles else 0.0
        recall = correct_count / len(expected_titles) if expected_titles else 1.0
        
        precisions.append(precision)
        recalls.append(recall)
        
        # Determine pass/fail
        fixture_passed = recall >= 0.8
        if fixture_passed:
            passed += 1
        else:
            failed += 1
        
        status = "✓ PASS" if fixture_passed else "✗ FAIL"
        logger.info(
            f"{status} - '{name}' | "
            f"Extracted: {len(extracted_titles)} | "
            f"Expected: {len(expected_titles)} | "
            f"Correct: {correct_count} | "
            f"Precision: {precision:.2f} | "
            f"Recall: {recall:.2f}"
        )
    
    avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    
    return {
        "total_fixtures": total_fixtures,
        "passed": passed,
        "failed": failed,
        "avg_precision": round(avg_precision, 3),
        "avg_recall": round(avg_recall, 3)
    }


if __name__ == "__main__":
    logging.info("Running extraction evaluation suite...")
    results = run_evals()
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))
    
    exit_code = 1 if results["failed"] > 0 else 0
    sys.exit(exit_code)
