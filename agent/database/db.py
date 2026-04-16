import psycopg2
import psycopg2.extras
import logging
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Get a psycopg2 connection from DATABASE_URL env var."""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logging.error("DATABASE_URL not set in environment")
            return None
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        return None


def get_existing_jobs(jobs: list[dict]) -> set[tuple]:
    """Get set of (title, url) tuples for jobs already in database."""
    conn = get_connection()
    if not conn:
        return set()

    try:
        cursor = conn.cursor()
        existing = set()

        for job in jobs:
            title = job.get("title", "")
            url = job.get("url", "")
            cursor.execute(
                "SELECT id FROM jobs WHERE title = %s AND url = %s",
                (title, url)
            )
            if cursor.fetchone() is not None:
                existing.add((title, url))

        return existing

    except Exception as e:
        logging.warning(f"Could not check existing jobs: {e}")
        return set()
    finally:
        if conn:
            conn.close()


def filter_new_jobs(jobs: list[dict]) -> list[dict]:
    """Filter out jobs that already exist in database."""
    existing = get_existing_jobs(jobs)
    new_jobs = [
        job for job in jobs
        if (job.get("title", ""), job.get("url", "")) not in existing
    ]

    if existing:
        logging.info(
            f"Filtered jobs: {len(existing)} already seen, "
            f"{len(new_jobs)} new to score"
        )

    return new_jobs


def setup_tables():
    """Create jobs and agent_runs tables if they don't exist."""
    conn = get_connection()
    if not conn:
        logging.error("Cannot setup tables: connection failed")
        return

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT,
                url TEXT,
                description TEXT,
                score TEXT,
                reason TEXT,
                missing_skills TEXT,
                date_posted TEXT,
                scraped_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(title, url)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id SERIAL PRIMARY KEY,
                trace_id TEXT,
                pages_scraped INT,
                jobs_found INT,
                high_matches INT,
                medium_matches INT,
                email_sent BOOLEAN,
                run_at TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        logging.info("Tables created successfully")

    except Exception as e:
        logging.error(f"Failed to create tables: {e}")
    finally:
        if conn:
            conn.close()


def save_jobs(scored_jobs: list[dict]) -> int:
    """Save jobs to database, returning count of newly inserted jobs."""
    conn = get_connection()
    if not conn:
        logging.error("Cannot save jobs: connection failed")
        return 0

    try:
        cursor = conn.cursor()
        count = 0

        for job in scored_jobs:
            try:
                cursor.execute("""
                    INSERT INTO jobs 
                    (title, company, url, description, score, reason, missing_skills, date_posted)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (title, url) DO NOTHING
                """, (
                    job.get("title"),
                    job.get("company"),
                    job.get("url"),
                    job.get("description"),
                    job.get("score"),
                    job.get("reason"),
                    str(job.get("missing_skills", [])),
                    job.get("date_posted"),
                ))
                if cursor.rowcount > 0:
                    count += 1
            except Exception as e:
                logging.warning(f"Failed to insert job {job.get('title')}: {e}")

        conn.commit()
        logging.info(f"Saved {count} new jobs to database")
        return count

    except Exception as e:
        logging.error(f"Failed to save jobs: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def save_run(run_result: dict) -> None:
    """Save agent run record to database."""
    conn = get_connection()
    if not conn:
        logging.error("Cannot save run: connection failed")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_runs
            (trace_id, pages_scraped, jobs_found, high_matches, medium_matches, email_sent)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            run_result.get("trace_id"),
            run_result.get("pages_scraped"),
            run_result.get("jobs_found"),
            run_result.get("high_matches"),
            run_result.get("medium_matches"),
            run_result.get("email_sent"),
        ))
        conn.commit()
        logging.info("Agent run saved to database")

    except Exception as e:
        logging.error(f"Failed to save run: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_tables()
    print("DB setup complete")
