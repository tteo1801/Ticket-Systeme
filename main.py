"""
Ticket System API - FastAPI + SQLite
Lance en local : uvicorn main:app --reload
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tickets.db")

app = FastAPI(title="Ticket System API", version="1.0.0")

# Autorise le frontend (hébergé ailleurs) à appeler cette API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Status(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            requester_name TEXT NOT NULL,
            requester_email TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            status TEXT NOT NULL DEFAULT 'open',
            priority TEXT NOT NULL DEFAULT 'medium',
            assignee TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


init_db()


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=3)
    requester_name: str
    requester_email: str
    category: str = "general"
    priority: Priority = Priority.medium


class TicketUpdate(BaseModel):
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    assignee: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class CommentCreate(BaseModel):
    author: str
    body: str


def row_to_dict(row):
    return dict(row)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
def root():
    return {"message": "Ticket System API", "docs": "/docs"}


@app.post("/tickets", status_code=201)
def create_ticket(payload: TicketCreate):
    conn = get_db()
    now = now_iso()
    cur = conn.execute(
        """INSERT INTO tickets (title, description, requester_name, requester_email,
           category, status, priority, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (payload.title, payload.description, payload.requester_name, payload.requester_email,
         payload.category, Status.open.value, payload.priority.value, now, now)
    )
    conn.commit()
    ticket_id = cur.lastrowid
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


@app.get("/tickets")
def list_tickets(
    status: Optional[Status] = None,
    priority: Optional[Priority] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    conn = get_db()
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status.value)
    if priority:
        query += " AND priority = ?"
        params.append(priority.value)
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Ticket introuvable")
    comments = conn.execute(
        "SELECT * FROM comments WHERE ticket_id = ? ORDER BY created_at ASC", (ticket_id,)
    ).fetchall()
    conn.close()
    result = row_to_dict(row)
    result["comments"] = [row_to_dict(c) for c in comments]
    return result


@app.put("/tickets/{ticket_id}")
def update_ticket(ticket_id: int, payload: TicketUpdate):
    conn = get_db()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Ticket introuvable")
    updates = {k: (v.value if isinstance(v, Enum) else v)
               for k, v in payload.dict(exclude_unset=True).items()}
    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        values.append(now_iso())
        values.append(ticket_id)
        conn.execute(f"UPDATE tickets SET {set_clause}, updated_at = ? WHERE id = ?", values)
        conn.commit()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


@app.delete("/tickets/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Ticket introuvable")
    conn.execute("DELETE FROM comments WHERE ticket_id = ?", (ticket_id,))
    conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    return None


@app.post("/tickets/{ticket_id}/comments", status_code=201)
def add_comment(ticket_id: int, payload: CommentCreate):
    conn = get_db()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Ticket introuvable")
    now = now_iso()
    cur = conn.execute(
        "INSERT INTO comments (ticket_id, author, body, created_at) VALUES (?, ?, ?, ?)",
        (ticket_id, payload.author, payload.body, now)
    )
    conn.execute("UPDATE tickets SET updated_at = ? WHERE id = ?", (now, ticket_id))
    conn.commit()
    comment_id = cur.lastrowid
    crow = conn.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    conn.close()
    return row_to_dict(crow)


@app.get("/stats")
def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]
    by_status = conn.execute("SELECT status, COUNT(*) AS c FROM tickets GROUP BY status").fetchall()
    by_priority = conn.execute("SELECT priority, COUNT(*) AS c FROM tickets GROUP BY priority").fetchall()
    conn.close()
    return {
        "total": total,
        "by_status": {r["status"]: r["c"] for r in by_status},
        "by_priority": {r["priority"]: r["c"] for r in by_priority},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
