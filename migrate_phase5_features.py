"""Migration Phase 5 — create tables: review, conversation, message, show_view, notification."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db

TABLES_SQL = {
    "review": """
        CREATE TABLE IF NOT EXISTS review (
            id SERIAL PRIMARY KEY,
            show_id INTEGER NOT NULL REFERENCES shows(id),
            user_id INTEGER REFERENCES users(id),
            author_name VARCHAR(100) NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS ix_review_show_id ON review(show_id);
        CREATE INDEX IF NOT EXISTS ix_review_approved ON review(approved);
    """,
    "conversation": """
        CREATE TABLE IF NOT EXISTS conversation (
            id SERIAL PRIMARY KEY,
            user1_id INTEGER NOT NULL REFERENCES users(id),
            user2_id INTEGER NOT NULL REFERENCES users(id),
            show_id INTEGER REFERENCES shows(id),
            subject VARCHAR(200),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS ix_conversation_user1 ON conversation(user1_id);
        CREATE INDEX IF NOT EXISTS ix_conversation_user2 ON conversation(user2_id);
    """,
    "message": """
        CREATE TABLE IF NOT EXISTS message (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL REFERENCES conversation(id),
            sender_id INTEGER NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS ix_message_conversation ON message(conversation_id);
    """,
    "show_view": """
        CREATE TABLE IF NOT EXISTS show_view (
            id SERIAL PRIMARY KEY,
            show_id INTEGER NOT NULL REFERENCES shows(id),
            session_id VARCHAR(64),
            ip_hash VARCHAR(64),
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS ix_show_view_show_id ON show_view(show_id);
        CREATE INDEX IF NOT EXISTS ix_show_view_created ON show_view(created_at);
    """,
    "notification": """
        CREATE TABLE IF NOT EXISTS notification (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            body TEXT,
            link VARCHAR(300),
            read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS ix_notification_user ON notification(user_id);
        CREATE INDEX IF NOT EXISTS ix_notification_read ON notification(read);
    """,
}

def migrate():
    with app.app_context():
        for name, sql in TABLES_SQL.items():
            try:
                db.session.execute(db.text(sql))
                db.session.commit()
                print(f"  ✅ Table '{name}' créée / vérifiée")
            except Exception as e:
                db.session.rollback()
                print(f"  ⚠️  Table '{name}': {e}")

if __name__ == "__main__":
    print("🚀 Migration Phase 5 — Fonctionnalités Avancées")
    migrate()
    print("✅ Migration terminée")
