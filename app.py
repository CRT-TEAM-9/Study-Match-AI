"""
Nexus — Flask Backend Application Entry Point
=========================================================
Serves the custom HTML templates and exposes REST API endpoints
for the database, matching engine, and LLM chatbot operations.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import re
import uuid
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Import backend modules
from database.db_helper import load_students, save_student, find_student_by_id, get_next_student_id
from backend.matching_engine import find_matches, find_study_groups
from backend.llm_orchestrator import LLMOrchestrator
from backend.config import REGISTRATION_FIELDS
from database.db_helper_extended import (
    load_sessions,
    save_session,
    load_chats,
    save_message,
    load_tickets,
    save_ticket,
    create_group_chat,
    rename_group_chat,
    remove_participant_from_group,
    load_notifications,
    save_notification,
    delete_notification
)
import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
# Flask will serve files directly from the nexus directory as static assets
app = Flask(__name__, static_folder='nexus', static_url_path='')
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize LLM Orchestrator safely
try:
    orchestrator = LLMOrchestrator()
    has_llm = True
except Exception:
    orchestrator = None
    has_llm = False

# ──────────────────────────────────────────────
#  Page Routes
# ──────────────────────────────────────────────

@app.route('/')
@app.route('/index.html')
def index():
    """Serve the Landing Page with dynamic database statistics."""
    students = load_students()
    total_students = len(students)
    total_matches = int(total_students * 1.5)
    total_groups = int(total_students / 2)
    
    try:
        # Load template and dynamically interpolate metrics
        landing_path = os.path.join(app.static_folder, "landing.html")
        with open(landing_path, "r", encoding="utf-8") as f:
            html = f.read()
        
        html = html.replace("1,248", f"{total_students:,}")
        html = html.replace("856", f"{total_matches:,}")
        html = html.replace("142", f"{total_groups:,}")
        html = html.replace("Join 1,200+ students already matching", f"Join {total_students:,}+ students already matching")
        return html
    except Exception as e:
        app.logger.error(f"Error loading landing page: {e}")
        return app.send_static_file('landing.html')

@app.route('/login.html')
def login():
    """Serve the login template."""
    return app.send_static_file('login.html')

@app.route('/register.html')
def register():
    """Serve the registration template."""
    return app.send_static_file('register.html')

@app.route('/dashboard.html')
def dashboard():
    """Serve the student directory dashboard."""
    return app.send_static_file('dashboard.html')

@app.route('/chatbot.html')
def chatbot():
    """Serve the chatbot matchmaker interface."""
    return app.send_static_file('chatbot.html')

@app.route('/how-it-works.html')
def how_it_works():
    """Serve the 'How it Works' documentation template."""
    return app.send_static_file('how-it-works.html')

@app.route('/firebase-config.js')
def firebase_config_js():
    """Dynamically serve Firebase client credentials as JavaScript variable."""
    config_js = f"""
    window.firebaseConfig = {{
        apiKey: "{os.getenv('FIREBASE_API_KEY', '')}",
        authDomain: "{os.getenv('FIREBASE_AUTH_DOMAIN', '')}",
        projectId: "{os.getenv('FIREBASE_PROJECT_ID', '')}",
        storageBucket: "{os.getenv('FIREBASE_STORAGE_BUCKET', '')}",
        messagingSenderId: "{os.getenv('FIREBASE_MESSAGING_SENDER_ID', '')}",
        appId: "{os.getenv('FIREBASE_APP_ID', '')}",
        measurementId: "{os.getenv('FIREBASE_MEASUREMENT_ID', '')}"
    }};
    """
    return config_js, 200, {'Content-Type': 'application/javascript'}


@app.errorhandler(404)
def page_not_found(e):
    """Serve custom 404 page for any unhandled routes."""
    return app.send_static_file('404.html'), 404



# ──────────────────────────────────────────────
#  REST API Endpoints
# ──────────────────────────────────────────────

@app.route('/api/students', methods=['GET'])
def api_get_students():
    """Retrieve all student profiles from the JSON database."""
    students = load_students()
    return jsonify(students)

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Retrieve active matching metrics from the database."""
    students = load_students()
    total_students = len(students)
    total_matches = int(total_students * 1.5)
    
    # Calculate exact study groups formed using matching engine
    groups = find_study_groups(students, min_size=3, threshold=40.0)
    total_groups = len(groups)
    
    return jsonify({
        "total_students": total_students,
        "total_matches": total_matches,
        "total_groups": total_groups
    })

@app.route('/api/register', methods=['POST'])
@app.route('/api/students', methods=['POST'])
def api_register_student():
    """Register a new student profile in the database."""
    try:
        data = request.json
        if not data:
            return jsonify({"detail": "No payload provided."}), 400
            
        # Extract fields
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        college = data.get("college", "").strip()
        year = data.get("year", "").strip()
        branch = data.get("branch", "").strip()
        subjects_strong_in = data.get("subjects_strong_in", [])
        subjects_needing_help_in = data.get("subjects_needing_help_in", [])
        study_style = data.get("study_style", "").strip()
        preferred_study_time = data.get("preferred_study_time", [])
        availability_days = data.get("availability_days", [])
        goal = data.get("goal", "").strip()
        communication_preference = data.get("communication_preference", "").strip()
        profile_pic = data.get("profile_pic", "").strip()
        social_links = data.get("social_links", {})
        profile_visibility = data.get("profile_visibility", "public").strip()
        
        # Validation
        if not name or not email or not college or not year or not branch or not study_style or not goal or not communication_preference:
            return jsonify({"detail": "Please fill out all required personal and academic details."}), 400
            
        if not subjects_strong_in or not subjects_needing_help_in:
            return jsonify({"detail": "Please specify at least one strong subject and one subject needing help."}), 400
            
        if not preferred_study_time or not availability_days:
            return jsonify({"detail": "Please select at least one study time and one available day."}), 400
            
        # Create student profile
        new_id = get_next_student_id()
        profile = {
            "student_id": new_id,
            "name": name,
            "email": email,
            "college": college,
            "year": year,
            "branch": branch,
            "subjects_strong_in": subjects_strong_in,
            "subjects_needing_help_in": subjects_needing_help_in,
            "study_style": study_style,
            "preferred_study_time": preferred_study_time,
            "availability_days": availability_days,
            "goal": goal,
            "communication_preference": communication_preference,
            "profile_pic": profile_pic,
            "social_links": social_links,
            "profile_visibility": profile_visibility
        }
        
        save_student(profile)
        return jsonify(profile)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@app.route('/api/students/update-avatar', methods=['POST'])
def api_update_avatar():
    """Update a student's profile picture."""
    try:
        data = request.json
        if not data:
            return jsonify({"detail": "No payload provided."}), 400
            
        student_id = data.get("student_id")
        profile_pic = data.get("profile_pic", "").strip()
        
        if not student_id:
            return jsonify({"detail": "Missing student ID."}), 400
            
        student = find_student_by_id(student_id)
        if not student:
            return jsonify({"detail": "Student profile not found."}), 404
            
        student["profile_pic"] = profile_pic
        save_student(student)
        return jsonify(student)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@app.route('/api/students/update', methods=['POST'])
def api_update_profile():
    """Update a student's complete profile details."""
    try:
        data = request.json
        if not data:
            return jsonify({"detail": "No payload provided."}), 400
            
        student_id = data.get("student_id")
        if not student_id:
            return jsonify({"detail": "Missing student ID."}), 400
            
        student = find_student_by_id(student_id)
        if not student:
            return jsonify({"detail": "Student profile not found."}), 404
            
        # Update allowed fields
        for field in ["name", "college", "year", "branch", "study_style", "goal", "communication_preference", "profile_visibility"]:
            if field in data:
                student[field] = data[field]
                
        # Update array fields
        for field in ["subjects_strong_in", "subjects_needing_help_in", "preferred_study_time", "availability_days"]:
            if field in data and isinstance(data[field], list):
                student[field] = data[field]
                
        # Update nested social links
        if "social_links" in data:
            student["social_links"] = data["social_links"]
            
        save_student(student)
        return jsonify(student)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@app.route('/api/public-profile/<student_id>', methods=['GET'])
def api_get_public_profile(student_id):
    """Retrieve a student's public profile."""
    student = find_student_by_id(student_id)
    if not student:
        return jsonify({"detail": "Profile not found."}), 404
        
    if student.get("profile_visibility", "public") != "public":
        return jsonify({"detail": "This profile is private."}), 403
        
    # Return a safe subset of the profile (exclude email or other highly sensitive data if needed, but for now we return it so they can be contacted)
    return jsonify(student)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat messages for match queries and general bot conversation."""
    data = request.json
    if not data:
        return jsonify({"response": "⚠️ Invalid request payload."}), 400
        
    student_id = data.get("student_id")
    message = data.get("message", "").strip()
    history = data.get("history", [])
    
    student = find_student_by_id(student_id)
    if not student:
        return jsonify({"response": "⚠️ Error: Active student profile not found in database. Please log in again."}), 404
        
    query = message.lower()
    
    # Trigger matching engine if query asks for matches or partner
    if "match" in query or "find" in query or "partner" in query or "group" in query:
        all_students = load_students()
        matches = find_matches(student, all_students, top_n=3, threshold=30.0)
        groups = find_study_groups(all_students, min_size=3, threshold=40.0)
        
        # Filter groups to show only those containing the current student
        user_groups = [g for g in groups if student_id in [m["student_id"] for m in g["members"]]]
        
        if has_llm and orchestrator:
            try:
                conversational_text = orchestrator.present_matches(student["name"], matches, user_groups)
            except Exception:
                conversational_text = "Here are the top matches computed by the Compatibility engine:"
        else:
            conversational_text = (
                f"📊 **Matching Engine Results for {student['name']}**<br><br>"
                "We analyzed schedule overlaps, goals, study styles, and subjects. "
                "Here are the best matches calculated from the database:"
            )
            
        return jsonify({
            "response": conversational_text,
            "matches": matches,
            "groups": user_groups
        })
    else:
        # General conversation
        if has_llm and orchestrator:
            try:
                # Convert message history to format expected by Groq client
                llm_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]
                response_text = orchestrator.chat(message, llm_history)
            except Exception as e:
                app.logger.error(f"Groq API error: {e}")
                response_text = "I received your message! I'm here to match study partners. Type 'match' to find compatible peers."
        else:
            response_text = (
                f"I hear you! I am configured to run in local matchmaker mode. "
                f"If you ask me to **'find matches'** or **'match'**, I will execute the 4-factor compatibility scoring engine "
                f"against the student directory. Try typing **'match'**!"
            )
            
        return jsonify({
            "response": response_text
        })

@app.route('/api/chat/register-step', methods=['POST'])
def api_chat_register_step():
    """Handle conversational step-by-step registration logic."""
    data = request.json
    if not data:
        return jsonify({"success": False, "prompt": "Invalid request payload."}), 400
        
    step = data.get("step", 0)
    message = data.get("message", "").strip()
    profile = data.get("profile", {})
    
    total_fields = len(REGISTRATION_FIELDS)
    if step >= total_fields:
        return jsonify({"success": False, "prompt": "Registration is already complete!"}), 400
        
    field = REGISTRATION_FIELDS[step]
    field_key = field["key"]
    
    # Process and validate user response
    val = message
    if field["type"] == "list":
        val = [item.strip() for item in val.split(",") if item.strip()]
    elif field["type"] == "multi-choice":
        matched = []
        words = [w.lower().strip() for w in val.split(",")]
        for opt in field["validation"]:
            for w in words:
                if w in opt.lower():
                    matched.append(opt)
        val = list(set(matched)) if matched else [field["validation"][0]]
    elif field["type"] == "choice":
        matched = field["validation"][0]
        for opt in field["validation"]:
            if val.lower() in opt.lower():
                matched = opt
                break
        val = matched
        
    profile[field_key] = val
    next_step = step + 1
    
    # If there are more fields, return the next prompt
    if next_step < total_fields:
        next_field = REGISTRATION_FIELDS[next_step]
        prompt = f"Got it! Now: **{next_field['prompt']}**"
        if next_field["validation"]:
            prompt += f"<br>Options: <em>" + ", ".join(next_field["validation"]) + "</em>"
            
        return jsonify({
            "success": True,
            "step": next_step,
            "profile": profile,
            "complete": False,
            "prompt": prompt
        })
    else:
        # Complete registration, save profile and log user in
        new_id = get_next_student_id()
        profile["student_id"] = new_id
        profile["email"] = f"{profile.get('name','student').lower().replace(' ', '')}@university.edu"
        
        # Verify structure validation holds
        try:
            save_student(profile)
        except Exception as e:
            return jsonify({"success": False, "prompt": f"Failed validation: {str(e)}"}), 400
            
        complete_msg = (
            "🎉 **Registration Complete!**<br><br>"
            f"Congratulations, your profile has been successfully saved to the database as student ID **{new_id}**!<br><br>"
            "I have logged you in. You can now toggle the objective in the sidebar to **'Find Study Partner'** to run the matching engine!"
        )
        
        return jsonify({
            "success": True,
            "step": next_step,
            "profile": profile,
            "complete": True,
            "response": complete_msg
        })


# ──────────────────────────────────────────────
#  Cooperative Learning Endpoints
# ──────────────────────────────────────────────

@app.route('/api/sessions', methods=['GET'])
def api_get_sessions():
    student_id = request.args.get("student_id")
    if not student_id:
        return jsonify({"detail": "Missing student_id query parameter."}), 400
    sessions = load_sessions()
    filtered = [
        s for s in sessions 
        if s.get("creator_id") == student_id or s.get("partner_id") == student_id or student_id in s.get("attendees", [])
    ]
    return jsonify(filtered)

@app.route('/api/sessions', methods=['POST'])
def api_create_session():
    data = request.json
    if not data:
        return jsonify({"detail": "No payload provided."}), 400
    
    title = data.get("title", "").strip()
    date = data.get("date", "").strip()
    time = data.get("time", "").strip()
    description = data.get("description", "").strip()
    partner_id = data.get("partner_id", "").strip()
    creator_id = data.get("creator_id", "").strip()
    
    if not title or not date or not time or not creator_id:
        return jsonify({"detail": "Missing required fields: title, date, time, creator_id."}), 400
    
    creator_name = "You"
    partner_name = "Study Partner"
    students = load_students()
    for std in students:
        if std.get("student_id") == creator_id:
            creator_name = std.get("name", "You")
        if std.get("student_id") == partner_id:
            partner_name = std.get("name", "Study Partner")
            
    session = {
        "title": title,
        "date": date,
        "time": time,
        "description": description,
        "partner_id": partner_id,
        "partner_name": partner_name,
        "creator_id": creator_id,
        "creator_name": creator_name,
        "attendees": [creator_id, partner_id] if partner_id else [creator_id]
    }
    saved = save_session(session)
    return jsonify(saved)

@app.route('/api/chats', methods=['GET'])
def api_get_chats():
    student_id = request.args.get("student_id")
    if not student_id:
        return jsonify({"detail": "Missing student_id query parameter."}), 400
        
    chats = load_chats()
    students = load_students()
    student_map = {s["student_id"]: s for s in students}
    
    user_chats = []
    for chat in chats:
        chat_id = chat.get("chat_id", "")
        participants = chat.get("participants", [])
        is_group = chat.get("is_group", False)
        group_name = chat.get("group_name", "")
        
        if not participants:
            if student_id in chat_id:
                if chat_id.startswith("DM_"):
                    participants = chat_id.split("_")[1:]
                else:
                    participants = [student_id]
        
        if student_id in participants or student_id in chat_id:
            other_participant = None
            for p in participants:
                if p != student_id:
                    other_participant = p
                    break
            
            if is_group:
                other_name = group_name if group_name else "Study Group"
                other_pic = ""
            else:
                other_name = "Study Partner"
                other_pic = ""
                if other_participant and other_participant in student_map:
                    other_name = student_map[other_participant].get("name", other_participant)
                    other_pic = student_map[other_participant].get("profile_pic", "")
                elif chat_id.startswith("DM_"):
                    parts = chat_id.split("_")[1:]
                    for p in parts:
                        if p != student_id and p in student_map:
                            other_name = student_map[p].get("name", p)
                            other_pic = student_map[p].get("profile_pic", "")
                            break
                        
            last_message = ""
            last_timestamp = ""
            if chat.get("messages"):
                last_msg_obj = chat["messages"][-1]
                last_message = last_msg_obj.get("content", "")
                last_timestamp = last_msg_obj.get("timestamp", "")
                
            user_chats.append({
                "chat_id": chat_id,
                "other_participant": other_participant,
                "other_name": other_name,
                "other_pic": other_pic,
                "participants": participants,
                "is_group": is_group,
                "group_name": group_name,
                "last_message": last_message,
                "last_timestamp": last_timestamp
            })
    user_chats.sort(key=lambda x: x["last_timestamp"], reverse=True)
    return jsonify(user_chats)

@app.route('/api/chats/create_group', methods=['POST'])
def api_create_group():
    data = request.json
    if not data:
        return jsonify({"detail": "No payload provided."}), 400
        
    student_ids = data.get("student_ids", [])
    group_name = data.get("group_name", "Study Group").strip()
    
    if not student_ids:
        return jsonify({"detail": "Missing student_ids."}), 400
        
    chat = create_group_chat(student_ids, group_name)
    return jsonify(chat)

@app.route('/api/chats/<chat_id>/rename', methods=['POST'])
def api_rename_group(chat_id):
    data = request.json
    new_name = data.get("new_name", "").strip()
    if not new_name:
        return jsonify({"detail": "Missing new_name."}), 400
        
    success = rename_group_chat(chat_id, new_name)
    if success:
        return jsonify({"detail": "Group renamed successfully."})
    return jsonify({"detail": "Chat not found or failed to rename."}), 404

@app.route('/api/chats/<chat_id>/leave', methods=['POST'])
def api_leave_group(chat_id):
    data = request.json
    student_id = data.get("student_id", "").strip()
    if not student_id:
        return jsonify({"detail": "Missing student_id."}), 400
        
    success = remove_participant_from_group(chat_id, student_id)
    if success:
        return jsonify({"detail": "Left group successfully."})
    return jsonify({"detail": "Chat not found or failed to leave."}), 404

@app.route('/api/chats/<chat_id>/messages', methods=['GET'])
def api_get_chat_messages(chat_id):
    chats = load_chats()
    for chat in chats:
        if chat.get("chat_id") == chat_id:
            return jsonify(chat.get("messages", []))
    return jsonify([])

@app.route('/api/chats/<chat_id>/messages', methods=['POST'])
def api_send_message(chat_id):
    data = request.json
    if not data:
        return jsonify({"detail": "No payload provided."}), 400
        
    sender_id = data.get("sender_id", "").strip()
    sender_name = data.get("sender_name", "").strip()
    content = data.get("content", "").strip()
    file_url = data.get("file_url", "").strip()
    file_name = data.get("file_name", "").strip()
    file_type = data.get("file_type", "").strip()
    
    if not sender_id or (not content and not file_url):
        return jsonify({"detail": "Missing required fields: sender_id and content or file."}), 400
        
    if not sender_name:
        student = find_student_by_id(sender_id)
        if student:
            sender_name = student.get("name", "User")
        else:
            sender_name = "User"
            
    message = {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": content,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    if file_url:
        message["file_url"] = file_url
        message["file_name"] = file_name
        message["file_type"] = file_type
    
    messages = save_message(chat_id, message)
    return jsonify(messages)

@app.route('/api/tickets', methods=['GET'])
def api_get_tickets():
    tickets = load_tickets()
    # Sort open tickets first, then sort by ticket_id descending
    tickets_sorted = sorted(tickets, key=lambda t: (t.get("status", "open") != "open", t.get("ticket_id", "")), reverse=True)
    return jsonify(tickets_sorted)

@app.route('/api/tickets', methods=['POST'])
def api_create_ticket():
    data = request.json
    if not data:
        return jsonify({"detail": "No payload provided."}), 400
        
    student_id = data.get("student_id", "").strip()
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    description = data.get("description", "").strip()
    
    if not student_id or not subject or not topic or not description:
        return jsonify({"detail": "Missing required fields: student_id, subject, topic, description."}), 400
        
    student = find_student_by_id(student_id)
    student_name = student.get("name", "Student") if student else "Student"
    
    ticket = {
        "student_id": student_id,
        "student_name": student_name,
        "subject": subject,
        "topic": topic,
        "description": description,
        "status": "open",
        "created_at": datetime.datetime.now().isoformat()
    }
    
    saved = save_ticket(ticket)
    return jsonify(saved)

@app.route('/api/tickets/<ticket_id>/close', methods=['POST'])
def api_close_ticket(ticket_id):
    tickets = load_tickets()
    target_ticket = None
    for t in tickets:
        if t.get("ticket_id") == ticket_id:
            target_ticket = t
            break
            
    if not target_ticket:
        return jsonify({"detail": "Ticket not found."}), 404
        
    target_ticket["status"] = "closed"
    save_ticket(target_ticket)
    return jsonify(target_ticket)


# ──────────────────────────────────────────────
#  Notifications & Message Requests Endpoints
# ──────────────────────────────────────────────

@app.route('/api/notifications', methods=['GET'])
def api_get_notifications():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"detail": "student_id is required"}), 400
        
    notifications = load_notifications()
    user_notifications = [n for n in notifications if n.get("recipient_id") == student_id]
    
    # Sort by created_at descending
    user_notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jsonify(user_notifications)

@app.route('/api/notifications', methods=['POST'])
def api_create_notification():
    data = request.json
    recipient_id = data.get("recipient_id")
    sender_name = data.get("sender_name")
    sender_email = data.get("sender_email")
    sender_id = data.get("sender_id")
    message = data.get("message")
    
    if not recipient_id or not message:
        return jsonify({"detail": "recipient_id and message are required"}), 400
        
    if not sender_id and not (sender_name and sender_email):
        return jsonify({"detail": "Either sender_id, or both sender_name and sender_email are required"}), 400
        
    new_notif = {
        "recipient_id": recipient_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "sender_id": sender_id,
        "message": message,
        "type": "message_request",
        "status": "pending",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    saved = save_notification(new_notif)
    return jsonify(saved), 201

@app.route('/api/notifications/<notification_id>/resolve', methods=['POST'])
def api_resolve_notification(notification_id):
    data = request.json
    action = data.get("action")  # 'accept' or 'decline'
    
    notifications = load_notifications()
    target = None
    for n in notifications:
        if n.get("notification_id") == notification_id:
            target = n
            break
            
    if not target:
        return jsonify({"detail": "Notification not found"}), 404
        
    if action == "accept":
        # If it's a registered user, create a chat
        sender_id = target.get("sender_id")
        recipient_id = target.get("recipient_id")
        if sender_id and recipient_id:
            chat_id = f"DM_{min(sender_id, recipient_id)}_{max(sender_id, recipient_id)}"
            initial_msg = {
                "sender_id": sender_id,
                "text": target.get("message", "Let's study together!"),
                "timestamp": target.get("created_at")
            }
            save_message(chat_id, initial_msg)
            
        target["status"] = "accepted"
        save_notification(target)
        # We can safely delete it or leave it as accepted. Let's delete it so it clears out.
        delete_notification(notification_id)
        
        return jsonify({
            "detail": "Accepted and chat created" if sender_id else "Accepted request",
            "chat_id": chat_id if sender_id and recipient_id else None
        })
        
    elif action == "decline":
        delete_notification(notification_id)
        return jsonify({"detail": "Declined and removed"})
        
    return jsonify({"detail": "Invalid action"}), 400

# ──────────────────────────────────────────────
#  File Upload Endpoints
# ──────────────────────────────────────────────

@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    if 'file' not in request.files:
        return jsonify({"detail": "No file part in the request."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"detail": "No selected file."}), 400
        
    if file:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        file_url = f"/uploads/{unique_filename}"
        
        return jsonify({
            "file_url": file_url,
            "file_name": filename,
            "file_type": file.content_type
        })

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    # Bind dynamically to the port provided by Cloud Run, fallback to 5000 for local runs
    port = int(os.environ.get("PORT", 5000))
    # Bind to 0.0.0.0 in production containers to accept incoming routing requests
    host = "0.0.0.0" if os.environ.get("PORT") else "localhost"
    app.run(host=host, port=port, debug=True)
