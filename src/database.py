import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DATABASE_URL_DEFAULT = "sqlite:///./data/db.sqlite"

def get_db_path(database_url: str) -> Path:
    """Extracts the file path from a SQLite database URL."""
    if database_url.startswith("sqlite:///"):
        return Path(database_url.replace("sqlite:///", ""))
    raise ValueError(f"Invalid SQLite database URL format: {database_url}")

def get_connection(database_url: str = DATABASE_URL_DEFAULT) -> sqlite3.Connection:
    """
    Establishes and returns a connection to the SQLite database.
    Ensures the directory for the database file exists.
    """
    db_path = get_db_path(database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def initialize_db(database_url: str = DATABASE_URL_DEFAULT):
    """
    Initializes the database schema by creating necessary tables.
    """
    conn = get_connection(database_url)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            user_prompt TEXT,
            config_used TEXT,
            review_feedback TEXT,
            deliverables_path TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_workflow_run(
    run_id: str,
    status: str,
    start_time: str,
    user_prompt: str,
    config_used: str,
    database_url: str = DATABASE_URL_DEFAULT
) -> int:
    """Inserts a new workflow run record into the database."""
    conn = get_connection(database_url)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO workflow_runs (run_id, status, start_time, user_prompt, config_used)
        VALUES (?, ?, ?, ?, ?)
    """, (run_id, status, start_time, user_prompt, config_used))
    conn.commit()
    last_row_id = cursor.lastrowid
    conn.close()
    return last_row_id

def update_workflow_run(
    run_id: str,
    status: Optional[str] = None,
    end_time: Optional[str] = None,
    review_feedback: Optional[str] = None,
    deliverables_path: Optional[str] = None,
    database_url: str = DATABASE_URL_DEFAULT
):
    """Updates an existing workflow run record."""
    conn = get_connection(database_url)
    cursor = conn.cursor()
    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status)
    if end_time:
        updates.append("end_time = ?")
        params.append(end_time)
    if review_feedback:
        updates.append("review_feedback = ?")
        params.append(review_feedback)
    if deliverables_path:
        updates.append("deliverables_path = ?")
        params.append(deliverables_path)
    
    if updates:
        query = f"UPDATE workflow_runs SET {', '.join(updates)} WHERE run_id = ?"
        params.append(run_id)
        cursor.execute(query, tuple(params))
        conn.commit()
    conn.close()

def get_workflow_run(run_id: str, database_url: str = DATABASE_URL_DEFAULT) -> Optional[Dict[str, Any]]:
    """Retrieves a single workflow run by its ID."""
    conn = get_connection(database_url)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_workflow_runs(database_url: str = DATABASE_URL_DEFAULT) -> List[Dict[str, Any]]:
    """Retrieves all workflow run records."""
    conn = get_connection(database_url)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workflow_runs ORDER BY start_time DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]