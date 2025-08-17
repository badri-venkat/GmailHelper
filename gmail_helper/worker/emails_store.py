import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional

from gmail_helper.common.config import config
from gmail_helper.common.contracts.emails_interface import EmailsInterface
from gmail_helper.common.utils.logger import get_logger

LOG = get_logger(__name__)


class EmailsStore(EmailsInterface):
    """
    SQLite implementation of EmailsInterface.
    Returns dictionaries for easy API serialization.
    """

    CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS emails (
        id TEXT PRIMARY KEY,
        thread_id TEXT,
        sender TEXT,
        subject TEXT,
        snippet TEXT,
        received_datetime TEXT
    );
    """

    UPSERT_SQL = """
    INSERT OR IGNORE INTO emails (id, thread_id, sender, subject, snippet, received_datetime)
    VALUES (:id, :thread_id, :sender, :subject, :snippet, :received_datetime)
    """

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        with self._conn() as conn:
            conn.execute(self.CREATE_SQL)
            conn.commit()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # --- EmailsInterface methods ---

    def insert_email(self, email: Dict) -> None:
        with self._conn() as conn:
            conn.execute(self.UPSERT_SQL, email)
            conn.commit()
            LOG.info("Stored email %s - %s", email["id"], email.get("subject", ""))

    def get_last_n_emails(self, n: int) -> List[Dict]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT * FROM emails ORDER BY received_datetime DESC LIMIT ?",
                (n,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_email_by_id(self, email_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            cur = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
            row = cur.fetchone()
            return dict(row) if row else None
