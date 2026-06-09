"""
Study Match AI — Flask Backend Application Entry Point
=========================================================
Serves the custom HTML frontend templates and exposes REST API endpoints
for the database, matching engine, and LLM chatbot operations.
"""

from flask import Flask, jsonify, request, send_from_directory
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Import backend modules
from database.db_helper import load_students, save_student, find_student_by_id, get_next_student_id
from backend.matching_engine import find_matches, find_study_groups
from backend.llm_orchestrator import LLMOrchestrator
from backend.config import REGISTRATION_FIELDS

# Load environment variables
load_dotenv()

# Initialize Flask app
# Flask will serve files directly from the frontend directory as static assets
app = Flask(__name__, static_folder='frontend', static_url_path='')

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
        year = data.get("year", "").strip()
        branch = data.get("branch", "").strip()
        subjects_strong_in = data.get("subjects_strong_in", [])
        subjects_needing_help_in = data.get("subjects_needing_help_in", [])
        study_style = data.get("study_style", "").strip()
        preferred_study_time = data.get("preferred_study_time", [])
        availability_days = data.get("availability_days", [])
        goal = data.get("goal", "").strip()
        communication_preference = data.get("communication_preference", "").strip()
        
        # Validation
        if not name or not email or not year or not branch or not study_style or not goal or not communication_preference:
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
            "year": year,
            "branch": branch,
            "subjects_strong_in": subjects_strong_in,
            "subjects_needing_help_in": subjects_needing_help_in,
            "study_style": study_style,
            "preferred_study_time": preferred_study_time,
            "availability_days": availability_days,
            "goal": goal,
            "communication_preference": communication_preference
        }
        
        save_student(profile)
        return jsonify(profile)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

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


if __name__ == "__main__":
    # Start the Flask development server on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
