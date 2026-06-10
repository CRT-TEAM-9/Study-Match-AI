"""
Verify Extended Database Helpers
=================================
Runs automated checks against sessions, chats, and tickets helpers.
"""

import sys
import os

# Append workspace directory to system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_helper_extended import (
    load_sessions,
    save_session,
    load_chats,
    save_message,
    load_tickets,
    save_ticket
)

def run_tests():
    print("🚀 Starting Extended Database Helper Tests...")

    # 1. Test Ticket Operations
    print("\n--- Testing Help Request Tickets ---")
    tickets_before = load_tickets()
    print(f"Initial tickets count: {len(tickets_before)}")

    new_ticket = {
        "student_id": "STU999",
        "student_name": "Test Student",
        "subject": "Aerospace Engineering",
        "topic": "Orbital Mechanics",
        "description": "Struggling with Hohmann transfer calculations. Need help ASAP.",
        "status": "open",
        "created_at": "2026-06-09T20:00:00Z"
    }

    saved_ticket = save_ticket(new_ticket)
    print(f"Saved Ticket: {saved_ticket}")
    assert saved_ticket.get("ticket_id") is not None, "Failed to generate ticket_id"
    assert saved_ticket["status"] == "open"

    tickets_after = load_tickets()
    print(f"Tickets count after save: {len(tickets_after)}")
    assert len(tickets_after) == len(tickets_before) + 1, "Ticket count mismatch"

    # Close ticket
    saved_ticket["status"] = "closed"
    updated_ticket = save_ticket(saved_ticket)
    print(f"Closed Ticket: {updated_ticket}")
    assert updated_ticket["status"] == "closed"

    # 2. Test Scheduler / Sessions
    print("\n--- Testing Scheduler / Sessions ---")
    sessions_before = load_sessions()
    print(f"Initial sessions count: {len(sessions_before)}")

    new_session = {
        "title": "Orbital Mechanics Study Session",
        "date": "2026-06-15",
        "time": "14:00",
        "description": "Solving problem set 3.",
        "partner_id": "STU001",
        "partner_name": "Aarav Sharma",
        "creator_id": "STU999",
        "creator_name": "Test Student"
    }

    saved_session = save_session(new_session)
    print(f"Saved Session: {saved_session}")
    assert saved_session.get("session_id") is not None, "Failed to generate session_id"

    sessions_after = load_sessions()
    print(f"Sessions count after save: {len(sessions_after)}")
    assert len(sessions_after) == len(sessions_before) + 1, "Session count mismatch"

    # 3. Test Chats / Messages
    print("\n--- Testing Chat Rooms and Messages ---")
    chats_before = load_chats()
    print(f"Initial chats count: {len(chats_before)}")

    chat_id = "DM_STU001_STU999"
    msg = {
        "sender_id": "STU999",
        "sender_name": "Test Student",
        "content": "Hi Aarav! Thanks for accepting my help request.",
        "timestamp": "2026-06-09T20:05:00Z"
    }

    messages = save_message(chat_id, msg)
    print(f"Saved Message. Room history size: {len(messages)}")
    assert len(messages) >= 1
    assert messages[-1]["content"] == msg["content"]

    chats_after = load_chats()
    print(f"Chats count after save: {len(chats_after)}")
    
    # Verify participants were auto-populated
    found_chat = None
    for c in chats_after:
        if c.get("chat_id") == chat_id:
            found_chat = c
            break
    assert found_chat is not None, "Chat room not found in DB"
    print(f"Chat Room Participants: {found_chat.get('participants')}")
    assert "STU001" in found_chat.get("participants", []), "STU001 missing from participants"
    assert "STU999" in found_chat.get("participants", []), "STU999 missing from participants"

    print("\n✅ All Extended Database Helper tests passed successfully!")

if __name__ == "__main__":
    run_tests()
