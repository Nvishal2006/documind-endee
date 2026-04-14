import os
import json
import sqlite3
from typing import List, Dict, Any, Optional

DATA_DIR = os.environ.get("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "documind.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'processing'
            );
            
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                page INTEGER,
                chunk_index INTEGER,
                text TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Store BM25 structures per document to reconstruct BM25
            CREATE TABLE IF NOT EXISTS bm25_index (
                id INTEGER PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                tokens TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
            );
        """)

init_db()

# Operations
def add_document(doc_id: str, filename: str):
    with get_db() as conn:
        conn.execute("INSERT INTO documents (id, filename, status) VALUES (?, ?, ?)", (doc_id, filename, 'processing'))

def update_document_status(doc_id: str, status: str):
    with get_db() as conn:
        conn.execute("UPDATE documents SET status = ? WHERE id = ?", (status, doc_id))

def get_documents() -> List[Dict]:
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM documents ORDER BY upload_date DESC")
        return [dict(row) for row in cur.fetchall()]

def delete_document(doc_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.execute("DELETE FROM bm25_index WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))

def insert_chunk(chunk_id: str, doc_id: str, page: int, chunk_index: int, text: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chunks (id, doc_id, page, chunk_index, text) VALUES (?, ?, ?, ?, ?)",
            (chunk_id, doc_id, page, chunk_index, text)
        )

def insert_bm25_tokens(doc_id: str, chunk_id: str, tokens: List[str]):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO bm25_index (doc_id, chunk_id, tokens) VALUES (?, ?, ?)",
            (doc_id, chunk_id, json.dumps(tokens))
        )

def get_all_chunks() -> List[Dict]:
    with get_db() as conn:
        cur = conn.execute("SELECT c.*, d.filename FROM chunks c JOIN documents d ON c.doc_id = d.id")
        return [dict(row) for row in cur.fetchall()]
        
def get_bm25_data() -> List[Dict]:
    with get_db() as conn:
        cur = conn.execute("SELECT chunk_id, tokens FROM bm25_index")
        rows = cur.fetchall()
        return [{"chunk_id": row["chunk_id"], "tokens": json.loads(row["tokens"])} for row in rows]

def get_chunk_by_id(chunk_id: str) -> Optional[Dict]:
    with get_db() as conn:
        cur = conn.execute("SELECT c.*, d.filename FROM chunks c JOIN documents d ON c.doc_id = d.id WHERE c.id = ?", (chunk_id,))
        row = cur.fetchone()
        return dict(row) if row else None
