"""
Study Match AI — LLM Orchestrator
====================================
Manages all interactions with the Groq API for conversational AI features.

Responsibilities:
    1. Registration Flow — Drive step-by-step profile collection via natural conversation.
    2. Match Presentation — Transform raw match data into engaging, friendly output.
    3. General Chat — Handle greetings, mode selection, and off-topic gracefully.

The orchestrator uses a carefully crafted system prompt to maintain persona
consistency and ensure reliable structured data extraction from user responses.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from groq import Groq, APIError, APIConnectionError, RateLimitError

from backend.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
    VALID_STUDY_STYLES,
    VALID_GOALS,
    VALID_STUDY_TIMES,
    VALID_DAYS,
    VALID_COMMUNICATION_PREFS,
    VALID_YEARS,
    REGISTRATION_FIELDS,
)

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SYSTEM PROMPTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_PROMPT_MAIN = """You are Study Match AI, a friendly and enthusiastic academic advisor chatbot. Your personality is warm, encouraging, and slightly nerdy — you genuinely love helping students find the perfect study partners.

CORE RULES:
1. You help students with TWO modes: "Register" (create their profile) and "Find Match" (discover study partners).
2. When greeting a new user, warmly introduce yourself and ask them to choose between registering or finding a match.
3. Keep responses concise but friendly — 2-4 sentences max unless presenting match results.
4. Use emojis sparingly but effectively to keep the tone upbeat.
5. NEVER make up student data or matches. Only reference real data provided to you.
6. If a user asks something off-topic, gently redirect them to registration or matching.

IMPORTANT: You are ONLY a study group matchmaker. You do NOT tutor, solve homework, or answer academic questions."""

SYSTEM_PROMPT_REGISTRATION = """You are guiding a student through profile registration. Collect information ONE field at a time through natural conversation.

CURRENT TASK: Collect the value for the field "{field_name}".
FIELD DESCRIPTION: {field_prompt}
FIELD TYPE: {field_type}
{valid_options}

ALREADY COLLECTED DATA:
{collected_data}

RULES FOR THIS INTERACTION:
1. Ask for ONLY the current field in a natural, conversational way.
2. If the field has valid options, present them clearly but conversationally.
3. Be encouraging and acknowledge the student's previous answers when transitioning.
4. If the student's response doesn't match valid options (for choice fields), gently ask them to choose from the available options.
5. Keep your response to 2-3 sentences maximum.
6. Do NOT skip ahead to ask about other fields."""

SYSTEM_PROMPT_EXTRACTION = """You are a data extraction assistant. Your ONLY job is to extract structured data from a user's conversational response.

TASK: Extract the value for the field "{field_name}" from the user's message.
FIELD TYPE: {field_type}
{valid_options}

RULES:
1. Return ONLY valid JSON — no other text, no markdown, no explanation.
2. For "text" type: Return {{"value": "extracted text", "confidence": "high"|"medium"|"low"}}
3. For "choice" type: Return {{"value": "matched option", "confidence": "high"|"medium"|"low"}}
4. For "list" type: Return {{"value": ["item1", "item2"], "confidence": "high"|"medium"|"low"}}
5. For "multi-choice" type: Return {{"value": ["selected1", "selected2"], "confidence": "high"|"medium"|"low"}}
6. If you cannot confidently extract the data, return {{"value": null, "confidence": "low", "reason": "brief explanation"}}
7. Normalize choices to match the valid options exactly (case-insensitive matching).
8. For list/multi-choice, the user might separate items with commas, "and", or newlines — handle all formats."""

SYSTEM_PROMPT_MATCH_PRESENTATION = """You are presenting study partner match results to a student. Make it exciting and encouraging!

STUDENT NAME: {student_name}
MATCH RESULTS:
{match_data}

RULES:
1. Present the results with enthusiasm — this is like revealing a great surprise!
2. Highlight the TOP reason why each match is good (from the breakdown data).
3. Use the compatibility scores but make them feel human (e.g., "You two are a 78% match — that's really strong!").
4. If there are study group suggestions, present them as a bonus discovery.
5. If no matches were found, be empathetic and suggest specific actions (e.g., "Try adding more available days" or "Consider broadening your study style preference").
6. Keep it concise — summarize, don't dump raw data.
7. End by asking if they'd like to explore any match further or adjust their profile."""

SYSTEM_PROMPT_COMPLETION = """You are congratulating a student on completing their registration profile.

REGISTERED PROFILE:
{profile_data}

RULES:
1. Celebrate the completion with genuine enthusiasm!
2. Provide a brief, clean summary of their profile.
3. Let them know they can now use "Find Match" to discover study partners.
4. Keep it to 3-4 sentences plus the profile summary.
5. Use a visual format for the summary (bullet points or similar)."""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ORCHESTRATOR CLASS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class LLMOrchestrator:
    """
    Manages all LLM interactions using the Groq API.

    Handles conversation flow, data extraction, and response generation
    with proper error handling and retry logic.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the orchestrator with a Groq API key.

        Args:
            api_key: Groq API key. Falls back to config if not provided.

        Raises:
            ValueError: If no API key is available.
        """
        self._api_key = api_key or GROQ_API_KEY
        if not self._api_key or self._api_key == "your_groq_api_key_here":
            raise ValueError(
                "Groq API key is not configured. "
                "Please set GROQ_API_KEY in your .env file. "
                "Get a key from: https://console.groq.com/keys"
            )

        self._client = Groq(api_key=self._api_key)
        self._model = GROQ_MODEL

    # ──────────────────────────────────────────
    #  Core API call
    # ──────────────────────────────────────────

    def _call_llm(
        self,
        messages: list[dict[str, str]],
        temperature: float = GROQ_TEMPERATURE,
        max_tokens: int = GROQ_MAX_TOKENS,
        json_mode: bool = False,
    ) -> str:
        """
        Make a single call to the Groq API with error handling.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature (0.0–1.0).
            max_tokens: Maximum tokens in response.
            json_mode: If True, forces JSON output format.

        Returns:
            The assistant's response text.

        Raises:
            ConnectionError: If the API is unreachable.
            RuntimeError: For unexpected API errors.
        """
        try:
            kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self._client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content
            if content is None:
                return ""
            return content.strip()

        except APIConnectionError as e:
            logger.error("Groq API connection error: %s", e)
            raise ConnectionError(
                "Could not connect to Groq API. Please check your internet connection."
            ) from e

        except RateLimitError as e:
            logger.warning("Groq API rate limit hit: %s", e)
            raise RuntimeError(
                "Rate limit reached. Please wait a moment and try again."
            ) from e

        except APIError as e:
            logger.error("Groq API error: %s", e)
            raise RuntimeError(
                f"An error occurred with the AI service: {e.message}"
            ) from e

    # ──────────────────────────────────────────
    #  Greeting / Mode Selection
    # ──────────────────────────────────────────

    def generate_greeting(self) -> str:
        """
        Generate the initial chatbot greeting message.

        Returns:
            A friendly greeting string asking the user to choose a mode.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_MAIN},
            {
                "role": "user",
                "content": "Hi! I just opened the app for the first time.",
            },
        ]
        try:
            return self._call_llm(messages, temperature=0.8)
        except (ConnectionError, RuntimeError):
            # Graceful fallback if API is down
            return (
                "👋 Hey there! Welcome to **Study Match AI**!\n\n"
                "I'm here to help you find the perfect study partners. "
                "Here's what I can do:\n\n"
                "📝 **Register** — Create your study profile\n"
                "🔍 **Find Match** — Discover compatible study partners\n\n"
                "Which would you like to start with?"
            )

    # ──────────────────────────────────────────
    #  Registration Flow
    # ──────────────────────────────────────────

    def generate_field_prompt(
        self,
        field_index: int,
        collected_data: dict,
        conversation_history: list[dict[str, str]],
    ) -> str:
        """
        Generate a conversational prompt for the next registration field.

        Args:
            field_index: Index into REGISTRATION_FIELDS (0-based).
            collected_data: Fields already collected {key: value}.
            conversation_history: Previous messages in the conversation.

        Returns:
            A natural-language prompt asking for the next field.
        """
        if field_index >= len(REGISTRATION_FIELDS):
            return ""

        field = REGISTRATION_FIELDS[field_index]
        valid_options_str = ""
        if field["validation"]:
            options = ", ".join(field["validation"])
            valid_options_str = f"VALID OPTIONS: {options}"

        collected_str = (
            json.dumps(collected_data, indent=2)
            if collected_data
            else "Nothing collected yet — this is the first question."
        )

        system_prompt = SYSTEM_PROMPT_REGISTRATION.format(
            field_name=field["key"],
            field_prompt=field["prompt"],
            field_type=field["type"],
            valid_options=valid_options_str,
            collected_data=collected_str,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-6:],  # Keep last 6 messages for context
            {
                "role": "user",
                "content": f"Please ask me about my {field['key'].replace('_', ' ')}.",
            },
        ]

        try:
            return self._call_llm(messages, temperature=0.7)
        except (ConnectionError, RuntimeError):
            # Fallback to the static prompt
            fallback = field["prompt"]
            if field["validation"]:
                fallback += f"\n\nOptions: {', '.join(field['validation'])}"
            return fallback

    def extract_field_value(
        self,
        field_index: int,
        user_message: str,
    ) -> dict[str, Any]:
        """
        Extract structured field data from a user's conversational response.

        Uses JSON mode for reliable extraction.

        Args:
            field_index: Index into REGISTRATION_FIELDS.
            user_message: The user's raw text response.

        Returns:
            A dict with 'value' (extracted data) and 'confidence'.
            Value is None if extraction failed.
        """
        if field_index >= len(REGISTRATION_FIELDS):
            return {"value": None, "confidence": "low", "reason": "Invalid field index"}

        field = REGISTRATION_FIELDS[field_index]
        valid_options_str = ""
        if field["validation"]:
            options = ", ".join(field["validation"])
            valid_options_str = f"VALID OPTIONS: {options}"

        system_prompt = SYSTEM_PROMPT_EXTRACTION.format(
            field_name=field["key"],
            field_type=field["type"],
            valid_options=valid_options_str,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            raw_response = self._call_llm(
                messages,
                temperature=0.1,  # Low temp for accurate extraction
                max_tokens=256,
                json_mode=True,
            )

            result = json.loads(raw_response)

            # Post-process: validate against allowed options
            extracted = result.get("value")
            if extracted is not None and field["validation"]:
                extracted = self._normalize_to_valid_options(
                    extracted, field["validation"], field["type"]
                )
                result["value"] = extracted

            return result

        except (json.JSONDecodeError, ConnectionError, RuntimeError) as e:
            logger.warning("Field extraction failed: %s", e)
            return {
                "value": None,
                "confidence": "low",
                "reason": str(e),
            }

    def generate_completion_message(self, profile: dict) -> str:
        """
        Generate a celebration message after profile registration is complete.

        Args:
            profile: The completed student profile dict.

        Returns:
            A congratulatory message with profile summary.
        """
        profile_display = {
            k: v for k, v in profile.items() if k != "student_id"
        }

        system_prompt = SYSTEM_PROMPT_COMPLETION.format(
            profile_data=json.dumps(profile_display, indent=2)
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "I just finished registering!"},
        ]

        try:
            return self._call_llm(messages, temperature=0.8)
        except (ConnectionError, RuntimeError):
            # Fallback
            return (
                "🎉 **Registration Complete!**\n\n"
                f"Welcome aboard, **{profile.get('name', 'student')}**! "
                "Your profile has been saved successfully.\n\n"
                f"• **Year:** {profile.get('year', 'N/A')}\n"
                f"• **Branch:** {profile.get('branch', 'N/A')}\n"
                f"• **Strong in:** {', '.join(profile.get('subjects_strong_in', []))}\n"
                f"• **Needs help in:** {', '.join(profile.get('subjects_needing_help_in', []))}\n"
                f"• **Study Style:** {profile.get('study_style', 'N/A')}\n"
                f"• **Goal:** {profile.get('goal', 'N/A')}\n\n"
                "Switch to **Find Match** mode to discover your ideal study partners! 🔍"
            )

    # ──────────────────────────────────────────
    #  Match Presentation
    # ──────────────────────────────────────────

    def present_matches(
        self,
        student_name: str,
        matches: list[dict],
        groups: list[dict],
    ) -> str:
        """
        Generate an engaging presentation of match results.

        Args:
            student_name: The searching student's name.
            matches: List of match result dicts from the matching engine.
            groups: List of study group dicts from the matching engine.

        Returns:
            A conversational, formatted presentation of the results.
        """
        if not matches and not groups:
            return self._present_no_matches(student_name)

        # Prepare match data summary for the LLM
        match_summaries = []
        for i, match in enumerate(matches, 1):
            partner = match["partner"]
            summary = {
                "rank": i,
                "name": partner["name"],
                "year": partner["year"],
                "branch": partner["branch"],
                "score": match["overall_score"],
                "top_strengths": partner.get("subjects_strong_in", [])[:3],
                "breakdown": {
                    k: {
                        "score": v["score"],
                        "explanation": v["explanation"],
                    }
                    for k, v in match["breakdown"].items()
                },
            }
            match_summaries.append(summary)

        group_summaries = []
        for group in groups:
            group_summaries.append({
                "members": [m["name"] for m in group["members"]],
                "avg_score": group["avg_score"],
                "shared_traits": group["shared_traits"],
            })

        match_data = json.dumps(
            {"matches": match_summaries, "groups": group_summaries},
            indent=2,
        )

        system_prompt = SYSTEM_PROMPT_MATCH_PRESENTATION.format(
            student_name=student_name,
            match_data=match_data,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Show me my study partner matches!",
            },
        ]

        try:
            return self._call_llm(messages, temperature=0.8, max_tokens=1500)
        except (ConnectionError, RuntimeError):
            # Fallback: present raw data nicely
            return self._fallback_match_presentation(
                student_name, matches, groups
            )

    def _present_no_matches(self, student_name: str) -> str:
        """Generate a friendly 'no matches found' message."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_MAIN},
            {
                "role": "user",
                "content": (
                    f"My name is {student_name} and the matching engine "
                    "found zero compatible study partners for me. "
                    "Please give me helpful suggestions for what to do."
                ),
            },
        ]

        try:
            return self._call_llm(messages, temperature=0.7)
        except (ConnectionError, RuntimeError):
            return (
                f"😔 Hey {student_name}, I couldn't find any matches that "
                "meet the compatibility threshold right now.\n\n"
                "Here are some tips to improve your chances:\n"
                "• **Add more available days** — flexibility helps a lot!\n"
                "• **Try a different study style** — 'discussion' tends to match well\n"
                "• **Broaden your time slots** — adding 'evening' opens up more options\n\n"
                "Would you like to update your profile? 📝"
            )

    def _fallback_match_presentation(
        self,
        student_name: str,
        matches: list[dict],
        groups: list[dict],
    ) -> str:
        """Fallback match presentation when the LLM is unavailable."""
        lines = [f"🎉 **Match Results for {student_name}**\n"]

        for i, match in enumerate(matches, 1):
            partner = match["partner"]
            score = match["overall_score"]
            lines.append(
                f"**#{i} — {partner['name']}** "
                f"({partner['year']}, {partner['branch']}) "
                f"— **{score}%** compatible"
            )
            lines.append(f"   {match['summary']}\n")

        if groups:
            lines.append("---\n")
            lines.append("👥 **Study Group Suggestions:**\n")
            for group in groups:
                member_names = ", ".join(m["name"] for m in group["members"])
                lines.append(
                    f"• **Group** ({group['avg_score']}% avg): {member_names}"
                )

        lines.append("\n_Would you like to explore any match further?_")
        return "\n".join(lines)

    # ──────────────────────────────────────────
    #  General chat
    # ──────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]],
    ) -> str:
        """
        Handle general chat messages outside of registration/matching flows.

        Args:
            user_message: The user's message.
            conversation_history: Previous messages for context.

        Returns:
            The assistant's response.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_MAIN},
            *conversation_history[-10:],  # Keep last 10 for context window
            {"role": "user", "content": user_message},
        ]

        try:
            return self._call_llm(messages)
        except (ConnectionError, RuntimeError) as e:
            return (
                "⚠️ I'm having trouble connecting to my AI brain right now. "
                "Please try again in a moment!\n\n"
                f"_Error: {e}_"
            )

    # ──────────────────────────────────────────
    #  Utility helpers
    # ──────────────────────────────────────────

    @staticmethod
    def _normalize_to_valid_options(
        value: Any,
        valid_options: list[str],
        field_type: str,
    ) -> Any:
        """
        Normalize extracted values to match valid options exactly.

        Handles case differences and fuzzy matching for common variations.

        Args:
            value: The extracted value (str or list).
            valid_options: List of valid option strings.
            field_type: The field type ("choice", "multi-choice", etc.)

        Returns:
            Normalized value matching valid options, or None if no match.
        """
        options_lower = {opt.lower(): opt for opt in valid_options}

        if field_type in ("choice",):
            if isinstance(value, str):
                normalized = options_lower.get(value.strip().lower())
                return normalized
            return None

        elif field_type in ("multi-choice", "list"):
            if isinstance(value, list):
                result = []
                for item in value:
                    if isinstance(item, str):
                        normalized = options_lower.get(item.strip().lower())
                        if normalized:
                            result.append(normalized)
                return result if result else None
            return None

        return value
