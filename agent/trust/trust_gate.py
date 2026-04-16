import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def should_send_email(scored_jobs: list[dict], digest: str) -> tuple[bool, str]:
    """
    Trust gate to decide if an email should be sent based on job extraction 
    and digest quality.
    
    Returns (True, "ok") if all checks pass.
    Returns (False, reason) if any check fails.
    """
    
    # Check 1: Jobs list is not empty
    if len(scored_jobs) == 0:
        return False, "No jobs to report"
    
    # Check 2: At least some high or medium matches
    high_count = sum(1 for j in scored_jobs if j.get("score") == "high")
    medium_count = sum(1 for j in scored_jobs if j.get("score") == "medium")
    if high_count + medium_count == 0:
        return False, "No high or medium matches found"
    
    # Check 3: Digest has reasonable length
    if len(digest) < 50:
        return False, "Digest too short — possible compose failure"
    
    # Check 4: Jobs count is reasonable (not a scraping error)
    max_jobs = int(os.getenv("TRUST_MAX_JOBS", "50"))
    if len(scored_jobs) > max_jobs:
        return False, f"Too many jobs ({len(scored_jobs)}) — possible scraping error"
    
    # All checks passed
    return True, "ok"


def log_audit(run_result: dict, allowed: bool, reason: str) -> None:
    """
    Log a structured audit entry for trust gate decision.
    """
    audit_log = (
        f"AUDIT | allowed={allowed} | reason={reason} | "
        f"jobs={run_result.get('jobs_found')} | "
        f"high={run_result.get('high_matches')} | "
        f"trace={run_result.get('trace_id')}"
    )
    logger.info(audit_log)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Trust Gate Test Cases")
    print("=" * 60)
    
    # Test case 1: Passing case with high matches
    print("\nTest 1: Valid run with high matches")
    jobs_valid = [
        {"title": "Senior Engineer", "score": "high", "reason": "Perfect fit"},
        {"title": "Engineer", "score": "medium", "reason": "Good fit"}
    ]
    digest_valid = "Long enough digest " * 5
    allowed, reason = should_send_email(jobs_valid, digest_valid)
    print(f"Result: allowed={allowed}, reason={reason}")
    run_result = {"jobs_found": len(jobs_valid), "high_matches": 1, "trace_id": "test-1"}
    log_audit(run_result, allowed, reason)
    
    # Test case 2: Failing case with no jobs
    print("\nTest 2: No jobs found")
    jobs_empty = []
    digest_empty = "Some digest"
    allowed, reason = should_send_email(jobs_empty, digest_empty)
    print(f"Result: allowed={allowed}, reason={reason}")
    run_result = {"jobs_found": 0, "high_matches": 0, "trace_id": "test-2"}
    log_audit(run_result, allowed, reason)
    
    # Test case 3: Failing case with no high/medium matches
    print("\nTest 3: Only low matches")
    jobs_low = [
        {"title": "Junior Engineer", "score": "low", "reason": "Not a fit"}
    ]
    digest_low = "Long enough digest " * 5
    allowed, reason = should_send_email(jobs_low, digest_low)
    print(f"Result: allowed={allowed}, reason={reason}")
    run_result = {"jobs_found": len(jobs_low), "high_matches": 0, "trace_id": "test-3"}
    log_audit(run_result, allowed, reason)
    
    # Test case 4: Failing case with digest too short
    print("\nTest 4: Digest too short")
    jobs_short_digest = [
        {"title": "Senior Engineer", "score": "high", "reason": "Perfect fit"}
    ]
    digest_short = "Too short"
    allowed, reason = should_send_email(jobs_short_digest, digest_short)
    print(f"Result: allowed={allowed}, reason={reason}")
    run_result = {"jobs_found": 1, "high_matches": 1, "trace_id": "test-4"}
    log_audit(run_result, allowed, reason)
    
    # Test case 5: Failing case with too many jobs
    print("\nTest 5: Too many jobs (possible error)")
    jobs_many = [
        {"title": f"Job {i}", "score": "high", "reason": "Fit"} 
        for i in range(100)
    ]
    digest_many = "Long enough digest " * 10
    allowed, reason = should_send_email(jobs_many, digest_many)
    print(f"Result: allowed={allowed}, reason={reason}")
    run_result = {"jobs_found": len(jobs_many), "high_matches": 100, "trace_id": "test-5"}
    log_audit(run_result, allowed, reason)
    
    print("\n" + "=" * 60)
    print("Trust gate tests completed")
    print("=" * 60)
