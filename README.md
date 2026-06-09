# 🎓 StudyMatch AI

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![Groq AI](https://img.shields.io/badge/Groq%20Cloud-F55A42?style=for-the-badge&logo=google-gemini&logoColor=white)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**StudyMatch AI** is a professional peer-matching platform designed for university students to form optimal study partnerships. The application leverages an intelligent weighted compatibility matrix alongside a conversational LLM agent to register student profiles dynamically and explain match recommendations interactively.

---

## 🌟 Key Features

*   **🗣️ Conversational AI Registration**: Students can set up their academic profile in a multi-turn conversation with an AI agent rather than filling out static form inputs.
*   **🧩 Intelligent Compatibility Matrix**: Calculates matching pairs based on a custom-weighted algorithm rather than random assignment.
*   **👥 Automated Study Groups**: Suggests study circles dynamically if 3 or more students share highly compatible study styles, availabilities, and goals.
*   **📊 Student Directory Dashboard**: Instant search, category filters, and compatibility ranking for peer profiles.
*   **🌓 Premium 3-State Theme Engine**:
    *   Cycle between **Light**, **Dark**, and **System** schemes.
    *   System mode integrates native browser/OS media query listeners (`(prefers-color-scheme: dark)`) for instant UI adjustment.
    *   Inline, blocking `<head>` configuration that prevents layout styling flashes (white/dark flashes) on initial page load.

---

## 📐 Matchmaking Algorithm & Weights

To prevent arbitrary student pairings, compatibility is calculated by evaluating specific logical intersections:

| Match Criteria | Weight | Description |
| :--- | :--- | :--- |
| **Complementary Strengths** | `40%` | Student A's weak subjects match Student B's strong subjects, and vice-versa. |
| **Time & Day Overlap** | `30%` | Evaluates shared study slots (e.g. evening, night) and availability days. |
| **Study Style Match** | `15%` | Checks compatibility between learning patterns (e.g. discussion, practice problems). |
| **Shared Goal Type** | `15%` | Assesses mutual objectives (e.g. exam prep, concept clarity, project collaboration). |

---

## 📁 Project Directory Structure

```text
Study Match AI/
│
├── backend/                  # Python backend core logic
│   ├── config.py             # Schema rules, fields, and constants
│   ├── llm_orchestrator.py   # Groq SDK LLM agent router and states
│   └── matching_engine.py    # Pairwise compatibility scores & group finder
│
├── database/                 # JSON file-based storage layer
│   ├── db_helper.py          # Read/write queries for profile database
│   └── students.json         # Complete dataset of student profiles
│
├── frontend/                 # Client-side static mockups & CSS
│   ├── landing.html          # Dynamic portal entry showing platform stats
│   ├── login.html            # Profile selector screen
│   ├── register.html         # Custom registration form & JS payload parser
│   ├── dashboard.html        # Interactive peer search directory table
│   └── chatbot.html          # LLM interface for chatbot registration/matching
│
├── .env                      # Application environment variables (Git ignored)
├── app.py                    # Flask development server entry point
├── verify_backend.py         # Verification suite for matching engine
├── requirements.txt          # Python package requirements list
└── README.md                 # Project README documentation
```

---

## 🚀 Getting Started

Follow these instructions to run the application locally.

### 1. Prerequisites
- Python 3.9+
- A valid **Groq Cloud API Key** (to run the conversational registration chatbot)

### 2. Installation & Environment Setup

Clone the repository and navigate to the project root:
```bash
# Set up a Python Virtual Environment
python -m venv .venv

# Activate the Virtual Environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate the Virtual Environment (Windows CMD)
.\.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 3. API Key Setup

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run the Dev Server

Start the Flask application server:
```bash
python app.py
```
By default, the server runs on: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Verification

To execute diagnostic scripts testing the database queries and matching compatibility scoring logic, run:
```bash
python verify_backend.py
```

---

## 📝 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) or the header badges for details.
