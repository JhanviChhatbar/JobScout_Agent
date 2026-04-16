import psycopg2
import psycopg2.extras
import logging
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def _get_connection():
    """Get a psycopg2 connection from DATABASE_URL env var."""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logging.error("DATABASE_URL not set in environment")
            return None
        conn = psycopg2.connect(database_url)
        conn.set_session(autocommit=False)
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        return None


def setup_vector_tables():
    """Create vector extension and vector tables if they don't exist."""
    conn = _get_connection()
    if not conn:
        logging.error("Cannot setup vector tables: connection failed")
        return

    try:
        cursor = conn.cursor()

        # Try to create extension, but don't fail if it doesn't exist
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        except Exception as e:
            logging.warning(f"Vector extension not available: {e}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_embeddings (
                id SERIAL PRIMARY KEY,
                job_title TEXT,
                job_description TEXT,
                score TEXT,
                reason TEXT,
                url TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experience_chunks (
                id SERIAL PRIMARY KEY,
                chunk_text TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        logging.info("Vector tables created")

    except Exception as e:
        logging.warning(f"Vector table creation skipped (RAG may not be available): {e}")
    finally:
        if conn:
            conn.close()


def get_embedding(text: str) -> list[float]:
    """Get embedding for text using Gemini's embedding model.
    
    Returns empty list if embedding model is unavailable.
    This makes RAG optional - the agent continues without it.
    """
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        result = client.models.embed_content(
            model="models/embedding-001",
            contents=text
        )
        return result.embeddings[0].values
    except Exception as e:
        logging.debug(f"Embedding unavailable (RAG disabled): {e}")
        return []


def store_job_embedding(job: dict) -> None:
    """Store job embedding in vector database.
    
    Silently skips if embeddings are unavailable.
    """
    conn = _get_connection()
    if not conn:
        return

    try:
        text_to_embed = f"{job.get('title', '')} {job.get('description', '')}"
        embedding = get_embedding(text_to_embed)

        # Skip if no embedding available (RAG disabled)
        if not embedding:
            return

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO job_embeddings
            (job_title, job_description, score, reason, url, embedding)
            VALUES (%s, %s, %s, %s, %s, %s::vector)
            ON CONFLICT DO NOTHING
        """, (
            job.get("title"),
            job.get("description"),
            job.get("score"),
            job.get("reason"),
            job.get("url"),
            json.dumps(embedding),
        ))

        conn.commit()

    except Exception as e:
        logging.debug(f"Job embedding skipped: {e}")
    finally:
        if conn:
            conn.close()


def get_similar_past_jobs(job_description: str, limit: int = 3) -> list[dict]:
    """Get similar past jobs using cosine similarity.
    
    Returns empty list if embeddings unavailable (RAG disabled).
    """
    conn = _get_connection()
    if not conn:
        return []

    try:
        embedding = get_embedding(job_description)
        if not embedding:
            return []

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT job_title, job_description, score, reason
            FROM job_embeddings
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (json.dumps(embedding), limit))

        results = cursor.fetchall()
        return [dict(row) for row in results]

    except Exception as e:
        logging.debug(f"Similar jobs lookup skipped: {e}")
        return []
    finally:
        if conn:
            conn.close()


def store_experience_chunks(experience: str) -> None:
    """Split experience into chunks and store embeddings.
    
    Silently skips if embeddings are unavailable.
    """
    conn = _get_connection()
    if not conn:
        return

    try:
        # Split by double newline
        chunks = [c.strip() for c in experience.split("\n\n")]
        # Filter short chunks
        chunks = [c for c in chunks if len(c) >= 20]

        if not chunks:
            return

        cursor = conn.cursor()
        stored_count = 0

        for chunk in chunks:
            try:
                embedding = get_embedding(chunk)
                # Skip chunk if no embedding available (RAG disabled)
                if not embedding:
                    continue

                cursor.execute("""
                    INSERT INTO experience_chunks
                    (chunk_text, embedding)
                    VALUES (%s, %s::vector)
                    ON CONFLICT DO NOTHING
                """, (
                    chunk,
                    json.dumps(embedding),
                ))
                stored_count += 1
            except Exception as e:
                logging.debug(f"Skipping experience chunk: {e}")

        conn.commit()

    except Exception as e:
        logging.debug(f"Experience chunks skipped: {e}")
    finally:
        if conn:
            conn.close()


def get_relevant_experience(job_description: str, limit: int = 3) -> str:
    """Get relevant experience chunks for a job using cosine similarity.
    
    Returns empty string if embeddings unavailable (RAG disabled).
    """
    conn = _get_connection()
    if not conn:
        return ""

    try:
        embedding = get_embedding(job_description)
        if not embedding:
            return ""

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT chunk_text
            FROM experience_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (json.dumps(embedding), limit))

        results = cursor.fetchall()
        chunks = [row["chunk_text"] for row in results]
        return "\n".join(chunks)

    except Exception as e:
        logging.debug(f"Experience lookup skipped: {e}")
        return ""
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_vector_tables()
    print("Vector store ready")
