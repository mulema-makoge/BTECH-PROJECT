import sqlite3
import json
from network import Message

DB_FILE = "chat_history.db"

def initialize_db():
    """
    Initializes the database and creates the messages table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            msg_id TEXT PRIMARY KEY,
            sender_pk TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            signature TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outgoing_queue (
            msg_id TEXT PRIMARY KEY,
            sender_pk TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            signature TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_message_to_queue(message):
    """
    Saves a Message object to the outgoing queue.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO outgoing_queue (msg_id, sender_pk, timestamp, content, signature)
        VALUES (?, ?, ?, ?, ?)
    """, (message.msg_id, message.sender_pk, message.timestamp, message.content, message.signature))
    conn.commit()
    conn.close()

def load_and_clear_queue():
    """
    Loads all messages from the outgoing queue, clears the queue,
    and returns the messages.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM outgoing_queue ORDER BY timestamp ASC")
    rows = cursor.fetchall()

    messages = []
    for row in rows:
        messages.append(Message(
            msg_id=row[0],
            sender_pk=row[1],
            timestamp=row[2],
            content=row[3],
            signature=row[4]
        ))

    cursor.execute("DELETE FROM outgoing_queue")
    conn.commit()
    conn.close()
    return messages

def save_message(message):
    """
    Saves a Message object to the database.
    Returns True if the message was saved, False if it was a duplicate.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO messages (msg_id, sender_pk, timestamp, content, signature)
            VALUES (?, ?, ?, ?, ?)
        """, (message.msg_id, message.sender_pk, message.timestamp, message.content, message.signature))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This occurs if the msg_id (PRIMARY KEY) already exists.
        return False
    finally:
        conn.close()

def load_all_messages():
    """
    Loads all messages from the database and returns them as a list of Message objects.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        messages.append(Message(
            msg_id=row[0],
            sender_pk=row[1],
            timestamp=row[2],
            content=row[3],
            signature=row[4]
        ))
    return messages
