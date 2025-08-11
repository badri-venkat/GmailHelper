import sqlite3
from contextlib import contextmanager


class EmailsStore:
    CREATE_EMAILS_TABLE = """
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                thread_id TEXT,
                sender TEXT,
                subject TEXT,
                snippet TEXT,
                received_datetime TEXT
            )
        """

    INSERT_INTO_EMAILS = """
                INSERT OR IGNORE INTO emails (id, thread_id, sender, subject, snippet, received_datetime)
                VALUES (?, ?, ?, ?, ?, ?)
            """

    SELECT_RECENT_K_MAILS = """
            SELECT * FROM emails 
            ORDER BY received_datetime 
            LIMIT ?
    """

    def __init__(self, db_name: str = "emails.db"):
        self.db_name = db_name

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(self.CREATE_EMAILS_TABLE)
            conn.commit()

    def insert_email(self, email_data):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(self.INSERT_INTO_EMAILS, email_data)
            conn.commit()

    def select_most_recent_k_mails(self, k: int):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(self.SELECT_RECENT_K_MAILS, (k,))
            return c.fetchall()
