"""
Nexus — Extended Database Helper
==================================
Thread-safe lock-controlled helper functions to manage JSON databases for:
1. Study Sessions / Scheduler
2. Chat Rooms & Messages
3. Help Request Board Tickets
"""

import json
import os
import threading
from typing import Optional

_DB_DIR = os.path.dirname(os.path.abspath(__file__))
_SESSIONS_PATH = os.path.join(_DB_DIR, "sessions_db.json")
_CHATS_PATH = os.path.join(_DB_DIR, "chats_db.json")
_TICKETS_PATH = os.path.join(_DB_DIR, "tickets_db.json")
_NOTIFICATIONS_PATH = os.path.join(_DB_DIR, "notifications_db.json")

# Lock for thread safety
_lock = threading.Lock()

# Helper for generic read
def _read_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []

# Helper for generic write
def _write_json(path: str, data: list) -> None:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp_path, path)

# ──────────────────────────────────────────────
#  1. Study Sessions / Scheduler
# ──────────────────────────────────────────────

def load_sessions() -> list[dict]:
    """Load all study sessions from sessions_db.json."""
    with _lock:
        return _read_json(_SESSIONS_PATH)

def save_session(session: dict) -> dict:
    """Save a study session. Generates session_id if missing."""
    with _lock:
        sessions = _read_json(_SESSIONS_PATH)
        
        if not session.get("session_id"):
            # Generate next session ID e.g., SES001
            max_num = 0
            for s in sessions:
                sid = s.get("session_id", "")
                if sid.startswith("SES"):
                    try:
                        num = int(sid[3:])
                        max_num = max(max_num, num)
                    except ValueError:
                        continue
            session["session_id"] = f"SES{max_num + 1:03d}"

        # Insert or update
        updated = False
        for i, s in enumerate(sessions):
            if s.get("session_id") == session["session_id"]:
                sessions[i] = session
                updated = True
                break
        if not updated:
            sessions.append(session)

        _write_json(_SESSIONS_PATH, sessions)
        return session

# ──────────────────────────────────────────────
#  2. Chat Rooms & Messages
# ──────────────────────────────────────────────

def load_chats() -> list[dict]:
    """Load all chat logs from chats_db.json."""
    with _lock:
        return _read_json(_CHATS_PATH)

def save_message(chat_id: str, message: dict) -> list[dict]:
    """
    Append a message to a chat room log.
    If the chat room does not exist in chats_db.json, it is created.
    """
    with _lock:
        chats = _read_json(_CHATS_PATH)
        
        # Find or create chat room
        found_chat = None
        for c in chats:
            if c.get("chat_id") == chat_id:
                found_chat = c
                break
                
        if not found_chat:
            participants = []
            if chat_id.startswith("DM_"):
                parts = chat_id.split("_")[1:]
                participants = [p for p in parts if p]
            else:
                sender_id = message.get("sender_id")
                participants = [sender_id] if sender_id else []
                
            found_chat = {
                "chat_id": chat_id,
                "participants": participants,
                "messages": []
            }
            chats.append(found_chat)
        elif "participants" not in found_chat or not found_chat["participants"]:
            participants = []
            if chat_id.startswith("DM_"):
                parts = chat_id.split("_")[1:]
                participants = [p for p in parts if p]
            else:
                sender_id = message.get("sender_id")
                participants = [sender_id] if sender_id else []
            found_chat["participants"] = participants

        found_chat["messages"].append(message)
        _write_json(_CHATS_PATH, chats)
        return found_chat["messages"]

def create_group_chat(participants: list, group_name: str) -> dict:
    import uuid
    with _lock:
        chats = _read_json(_CHATS_PATH)
        chat_id = f"GROUP_{uuid.uuid4().hex[:8]}"
        new_chat = {
            "chat_id": chat_id,
            "participants": participants,
            "group_name": group_name,
            "is_group": True,
            "messages": []
        }
        chats.append(new_chat)
        _write_json(_CHATS_PATH, chats)
        return new_chat

def rename_group_chat(chat_id: str, new_name: str) -> bool:
    with _lock:
        chats = _read_json(_CHATS_PATH)
        for c in chats:
            if c.get("chat_id") == chat_id:
                c["group_name"] = new_name
                _write_json(_CHATS_PATH, chats)
                return True
        return False

def remove_participant_from_group(chat_id: str, student_id: str) -> bool:
    with _lock:
        chats = _read_json(_CHATS_PATH)
        for c in chats:
            if c.get("chat_id") == chat_id:
                if "participants" in c and student_id in c["participants"]:
                    c["participants"].remove(student_id)
                    _write_json(_CHATS_PATH, chats)
                    return True
        return False

def add_participant_to_group(chat_id: str, student_id: str) -> bool:
    with _lock:
        chats = _read_json(_CHATS_PATH)
        for c in chats:
            if c.get("chat_id") == chat_id:
                if "participants" not in c:
                    c["participants"] = []
                if student_id not in c["participants"]:
                    c["participants"].append(student_id)
                    _write_json(_CHATS_PATH, chats)
                    return True
        return False

def update_typing_status(chat_id: str, student_id: str) -> bool:
    from datetime import datetime
    with _lock:
        chats = _read_json(_CHATS_PATH)
        for c in chats:
            if c.get("chat_id") == chat_id:
                if "typing_users" not in c:
                    c["typing_users"] = {}
                c["typing_users"][student_id] = datetime.utcnow().isoformat() + "Z"
                _write_json(_CHATS_PATH, chats)
                return True
        return False

def update_read_receipts(chat_id: str, student_id: str) -> bool:
    from datetime import datetime
    with _lock:
        chats = _read_json(_CHATS_PATH)
        for c in chats:
            if c.get("chat_id") == chat_id:
                if "read_receipts" not in c:
                    c["read_receipts"] = {}
                c["read_receipts"][student_id] = datetime.utcnow().isoformat() + "Z"
                _write_json(_CHATS_PATH, chats)
                return True
        return False

def delete_chat_message(chat_id: str, student_id: str, timestamp: str) -> bool:
    with _lock:
        chats = _read_json(_CHATS_PATH)
        for c in chats:
            if c.get("chat_id") == chat_id:
                # Find message by student_id and timestamp
                for i, m in enumerate(c.get("messages", [])):
                    if m.get("sender_id") == student_id and m.get("timestamp") == timestamp:
                        del c["messages"][i]
                        _write_json(_CHATS_PATH, chats)
                        return True
        return False

# ──────────────────────────────────────────────
#  3. Help Request Tickets
# ──────────────────────────────────────────────

def load_tickets() -> list[dict]:
    """Load all tickets from tickets_db.json."""
    with _lock:
        return _read_json(_TICKETS_PATH)

def save_ticket(ticket: dict) -> dict:
    """Save a ticket profile. Generates ticket_id if missing."""
    with _lock:
        tickets = _read_json(_TICKETS_PATH)
        
        if not ticket.get("ticket_id"):
            # Generate next ticket ID e.g., TCK001
            max_num = 0
            for t in tickets:
                tid = t.get("ticket_id", "")
                if tid.startswith("TCK"):
                    try:
                        num = int(tid[3:])
                        max_num = max(max_num, num)
                    except ValueError:
                        continue
            ticket["ticket_id"] = f"TCK{max_num + 1:03d}"

        # Insert or update
        updated = False
        for i, t in enumerate(tickets):
            if t.get("ticket_id") == ticket["ticket_id"]:
                tickets[i] = ticket
                updated = True
                break
        if not updated:
            tickets.append(ticket)

        _write_json(_TICKETS_PATH, tickets)
        return ticket

# ──────────────────────────────────────────────
#  4. Notifications & Message Requests
# ──────────────────────────────────────────────

def load_notifications() -> list[dict]:
    """Load all notifications from notifications_db.json."""
    with _lock:
        return _read_json(_NOTIFICATIONS_PATH)

def save_notification(notification: dict) -> dict:
    """Save a notification. Generates notification_id if missing."""
    with _lock:
        notifications = _read_json(_NOTIFICATIONS_PATH)
        
        if not notification.get("notification_id"):
            max_num = 0
            for n in notifications:
                nid = n.get("notification_id", "")
                if nid.startswith("NOT"):
                    try:
                        num = int(nid[3:])
                        max_num = max(max_num, num)
                    except ValueError:
                        continue
            notification["notification_id"] = f"NOT{max_num + 1:03d}"

        updated = False
        for i, n in enumerate(notifications):
            if n.get("notification_id") == notification["notification_id"]:
                notifications[i] = notification
                updated = True
                break
        if not updated:
            notifications.append(notification)

        _write_json(_NOTIFICATIONS_PATH, notifications)
        return notification

def delete_notification(notification_id: str) -> bool:
    """Delete a notification by ID."""
    with _lock:
        notifications = _read_json(_NOTIFICATIONS_PATH)
        new_list = [n for n in notifications if n.get("notification_id") != notification_id]
        if len(new_list) != len(notifications):
            _write_json(_NOTIFICATIONS_PATH, new_list)
            return True
        return False
