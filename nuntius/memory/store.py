import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


class MemoryStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    role TEXT,
                    content TEXT,
                    tool_calls TEXT,
                    created_at TEXT,
                    FOREIGN KEY (conv_id) REFERENCES conversations(id)
                )
            """)

    def create_conversation(self) -> str:
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, ?, ?)",
                (conv_id, now, now),
            )
        return conv_id

    def add_message(self, conv_id: str, role: str, content: str, tool_calls: list = None):
        now = datetime.now().isoformat()
        tc_json = json.dumps(tool_calls) if tool_calls else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (conv_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, role, content, tc_json, now),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conv_id),
            )

    def get_conversation(self, conv_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT role, content, tool_calls FROM messages WHERE conv_id = ? ORDER BY id",
                (conv_id,),
            ).fetchall()
        messages = []
        for role, content, tc_json in rows:
            msg = {"role": role, "content": content or ""}
            if tc_json:
                msg["tool_calls"] = json.loads(tc_json)
            messages.append(msg)
        return messages

    def list_conversations(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [{"id": r[0], "created_at": r[1], "updated_at": r[2]} for r in rows]
