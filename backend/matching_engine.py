"""
Study Match AI — Matching Engine
==================================
Deterministic, weighted compatibility algorithm for student matchmaking.

This module contains NO LLM calls — all scoring is pure logic based on
the weight matrix defined in the TRD:

    • Complementary Strengths:  40%
    • Time & Day Overlap:       30%
    • Study Style Compatibility: 15%
    • Shared Goal Type:         15%

Each factor produces a normalized 0.0–1.0 score. The final compatibility
percentage is the weighted sum × 100.
"""

from __future__ import annotations

from typing import Any

from backend.config import WEIGHTS, STYLE_COMPATIBILITY


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INDIVIDUAL FACTOR SCORING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _score_complementary_strengths(
    student_a: dict, student_b: dict
) -> tuple[float, str]:
    """
    Score how well two students' strengths complement each other's weaknesses.

    Bidirectional: checks both A→B and B→A, then averages.
    Subjects are compared case-insensitively.

    Returns:
        (score, explanation) where score is 0.0–1.0
    """
    a_weak = {s.strip().lower() for s in student_a.get("subjects_needing_help_in", [])}
    b_strong = {s.strip().lower() for s in student_b.get("subjects_strong_in", [])}
    b_weak = {s.strip().lower() for s in student_b.get("subjects_needing_help_in", [])}
    a_strong = {s.strip().lower() for s in student_a.get("subjects_strong_in", [])}

    # A's weaknesses covered by B's strengths
    a_to_b = a_weak & b_strong
    a_to_b_score = len(a_to_b) / max(len(a_weak), 1)

    # B's weaknesses covered by A's strengths
    b_to_a = b_weak & a_strong
    b_to_a_score = len(b_to_a) / max(len(b_weak), 1)

    score = (a_to_b_score + b_to_a_score) / 2.0

    # Build human-readable explanation
    explanations = []
    if a_to_b:
        subjects = ", ".join(s.title() for s in sorted(a_to_b))
        explanations.append(
            f"{student_b['name']} can help with: {subjects}"
        )
    if b_to_a:
        subjects = ", ".join(s.title() for s in sorted(b_to_a))
        explanations.append(
            f"{student_a['name']} can help with: {subjects}"
        )
    if not explanations:
        explanations.append("No direct subject complementarity found")

    return score, " | ".join(explanations)


def _score_time_day_overlap(
    student_a: dict, student_b: dict
) -> tuple[float, str]:
    """
    Score the overlap in preferred study times and available days.

    Time overlap and day overlap each contribute 50% to this factor.

    Returns:
        (score, explanation) where score is 0.0–1.0
    """
    a_times = set(student_a.get("preferred_study_time", []))
    b_times = set(student_b.get("preferred_study_time", []))
    a_days = set(student_a.get("availability_days", []))
    b_days = set(student_b.get("availability_days", []))

    time_overlap = a_times & b_times
    day_overlap = a_days & b_days

    max_times = max(len(a_times | b_times), 1)
    max_days = max(len(a_days | b_days), 1)

    time_score = len(time_overlap) / max_times
    day_score = len(day_overlap) / max_days

    score = (time_score + day_score) / 2.0

    # Explanation
    parts = []
    if time_overlap:
        parts.append(f"Shared times: {', '.join(sorted(time_overlap))}")
    else:
        parts.append("No overlapping study times")
    if day_overlap:
        parts.append(f"Shared days: {', '.join(sorted(day_overlap))}")
    else:
        parts.append("No overlapping days")

    return score, " | ".join(parts)


def _score_study_style(
    student_a: dict, student_b: dict
) -> tuple[float, str]:
    """
    Score study style compatibility using the predefined compatibility matrix.

    Returns:
        (score, explanation) where score is 0.0–1.0
    """
    style_a = student_a.get("study_style", "").strip().lower()
    style_b = student_b.get("study_style", "").strip().lower()

    if style_a == style_b:
        score = 1.0
        explanation = f"Same study style: {style_a}"
    else:
        score = STYLE_COMPATIBILITY.get((style_a, style_b), 0.0)
        if score >= 0.5:
            explanation = f"Compatible styles: {style_a} ↔ {style_b}"
        elif score > 0:
            explanation = f"Partially compatible: {style_a} ↔ {style_b}"
        else:
            explanation = f"Different styles: {style_a} vs {style_b}"

    return score, explanation


def _score_goal_match(
    student_a: dict, student_b: dict
) -> tuple[float, str]:
    """
    Score whether both students share the same study goal.

    Returns:
        (score, explanation) where score is 0.0 or 1.0
    """
    goal_a = student_a.get("goal", "").strip().lower()
    goal_b = student_b.get("goal", "").strip().lower()

    if goal_a == goal_b:
        return 1.0, f"Same goal: {goal_a}"
    else:
        return 0.0, f"Different goals: {goal_a} vs {goal_b}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COMPOSITE SCORING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def calculate_compatibility(student_a: dict, student_b: dict) -> dict[str, Any]:
    """
    Calculate the full compatibility score between two students.

    Args:
        student_a: First student profile dict.
        student_b: Second student profile dict.

    Returns:
        A dict with structure:
        {
            "overall_score": float (0–100),
            "partner": dict (student_b profile),
            "breakdown": {
                "complementary_strengths": {"score": float, "weighted": float, "explanation": str},
                "time_day_overlap":        {"score": float, "weighted": float, "explanation": str},
                "study_style":             {"score": float, "weighted": float, "explanation": str},
                "goal_match":              {"score": float, "weighted": float, "explanation": str},
            },
            "summary": str
        }
    """
    scorers = {
        "complementary_strengths": _score_complementary_strengths,
        "time_day_overlap":        _score_time_day_overlap,
        "study_style":             _score_study_style,
        "goal_match":              _score_goal_match,
    }

    breakdown: dict[str, dict] = {}
    total_weighted = 0.0

    for factor, scorer_fn in scorers.items():
        raw_score, explanation = scorer_fn(student_a, student_b)
        weight = WEIGHTS[factor]
        weighted_score = raw_score * weight

        breakdown[factor] = {
            "score": round(raw_score * 100, 1),
            "weighted": round(weighted_score * 100, 1),
            "weight_pct": int(weight * 100),
            "explanation": explanation,
        }
        total_weighted += weighted_score

    overall = round(total_weighted * 100, 1)

    # Generate a human-readable summary
    summary = generate_match_explanation(
        student_a["name"], student_b["name"], overall, breakdown
    )

    return {
        "overall_score": overall,
        "partner": student_b,
        "breakdown": breakdown,
        "summary": summary,
    }


def generate_match_explanation(
    name_a: str, name_b: str, score: float, breakdown: dict
) -> str:
    """
    Generate a structured, human-readable explanation of WHY a match is good.

    This text is displayed in the match cards and can also be fed to the
    LLM for conversational presentation.

    Args:
        name_a: Name of the searching student.
        name_b: Name of the matched partner.
        score: Overall compatibility score (0–100).
        breakdown: The per-factor breakdown dict.

    Returns:
        A multi-line explanation string.
    """
    lines = [f"🎯 {name_a} ↔ {name_b} — {score}% Compatible\n"]

    # Rank factors by contribution (highest first)
    ranked = sorted(
        breakdown.items(),
        key=lambda x: x[1]["weighted"],
        reverse=True,
    )

    factor_labels = {
        "complementary_strengths": "📚 Complementary Strengths",
        "time_day_overlap":        "🕐 Schedule Overlap",
        "study_style":             "📝 Study Style",
        "goal_match":              "🎯 Goal Alignment",
    }

    for factor, data in ranked:
        label = factor_labels.get(factor, factor)
        bar_filled = int(data["score"] / 10)
        bar_empty = 10 - bar_filled
        bar = "█" * bar_filled + "░" * bar_empty

        lines.append(
            f"  {label} [{bar}] {data['score']}% (weight: {data['weight_pct']}%)"
        )
        lines.append(f"    → {data['explanation']}")

    # Overall verdict
    if score >= 75:
        lines.append(f"\n✅ Excellent match! {name_b} is a highly compatible study partner.")
    elif score >= 50:
        lines.append(f"\n👍 Good match! {name_b} shares several key compatibilities.")
    elif score >= 30:
        lines.append(f"\n🤝 Moderate match. Some areas of compatibility with {name_b}.")
    else:
        lines.append(f"\n⚠️ Low compatibility with {name_b}. Consider broadening your criteria.")

    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TOP-LEVEL MATCHING API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def find_matches(
    target_student: dict,
    all_students: list[dict],
    top_n: int = 5,
    threshold: float = 30.0,
) -> list[dict]:
    """
    Find the best study partner matches for a target student.

    Args:
        target_student: The student seeking matches.
        all_students: All registered students (target will be excluded).
        top_n: Maximum number of matches to return.
        threshold: Minimum compatibility score (0–100) to include.

    Returns:
        A list of compatibility result dicts, sorted by score descending.
        Each dict has: overall_score, partner, breakdown, summary.
    """
    target_id = target_student.get("student_id", "")

    results = []
    for candidate in all_students:
        # Skip self
        if candidate.get("student_id", "") == target_id:
            continue

        result = calculate_compatibility(target_student, candidate)
        if result["overall_score"] >= threshold:
            results.append(result)

    # Sort by score, descending
    results.sort(key=lambda r: r["overall_score"], reverse=True)

    return results[:top_n]


def find_study_groups(
    all_students: list[dict],
    min_size: int = 3,
    threshold: float = 50.0,
) -> list[dict]:
    """
    Identify potential study groups — clusters of 3+ mutually compatible students.

    Uses a greedy approach: for each student, builds a candidate group from
    their top matches, then checks mutual compatibility within the group.

    Args:
        all_students: All registered student profiles.
        min_size: Minimum number of students in a group (default: 3).
        threshold: Minimum pairwise compatibility score to be considered
                   part of the same group.

    Returns:
        A list of group dicts, each containing:
        {
            "members": [student_dicts],
            "avg_score": float,
            "shared_traits": {
                "goals": [...],
                "study_styles": [...],
                "shared_days": [...],
                "shared_times": [...]
            }
        }
    """
    if len(all_students) < min_size:
        return []

    # Pre-compute pairwise compatibility scores
    n = len(all_students)
    scores: dict[tuple[str, str], float] = {}

    for i in range(n):
        for j in range(i + 1, n):
            id_a = all_students[i]["student_id"]
            id_b = all_students[j]["student_id"]
            result = calculate_compatibility(all_students[i], all_students[j])
            scores[(id_a, id_b)] = result["overall_score"]
            scores[(id_b, id_a)] = result["overall_score"]

    # Greedy group formation
    found_groups: list[dict] = []
    used_in_group: set[str] = set()  # Track students already in a group

    for anchor in all_students:
        anchor_id = anchor["student_id"]
        if anchor_id in used_in_group:
            continue

        # Find all candidates compatible with the anchor
        candidates = []
        for other in all_students:
            other_id = other["student_id"]
            if other_id == anchor_id:
                continue
            pair_score = scores.get((anchor_id, other_id), 0)
            if pair_score >= threshold:
                candidates.append(other)

        if len(candidates) < min_size - 1:
            continue

        # Build the group: start with anchor, greedily add compatible members
        group = [anchor]
        for candidate in sorted(
            candidates,
            key=lambda c: scores.get((anchor_id, c["student_id"]), 0),
            reverse=True,
        ):
            # Check if candidate is compatible with ALL existing group members
            is_compatible = all(
                scores.get((member["student_id"], candidate["student_id"]), 0)
                >= threshold
                for member in group
            )
            if is_compatible:
                group.append(candidate)

        if len(group) >= min_size:
            # Calculate group metrics
            member_ids = {m["student_id"] for m in group}

            # Avoid duplicate groups (check if this group is a subset of an existing one)
            is_duplicate = any(
                member_ids <= {m["student_id"] for m in existing["members"]}
                for existing in found_groups
            )
            if is_duplicate:
                continue

            # Average pairwise score
            pair_scores = []
            for i_idx in range(len(group)):
                for j_idx in range(i_idx + 1, len(group)):
                    pair_key = (group[i_idx]["student_id"], group[j_idx]["student_id"])
                    pair_scores.append(scores.get(pair_key, 0))

            avg_score = sum(pair_scores) / max(len(pair_scores), 1)

            # Shared traits
            shared_goals = _find_common_values(group, "goal")
            shared_styles = _find_common_values(group, "study_style")
            shared_days = _find_common_list_values(group, "availability_days")
            shared_times = _find_common_list_values(group, "preferred_study_time")

            found_groups.append({
                "members": group,
                "avg_score": round(avg_score, 1),
                "shared_traits": {
                    "goals": shared_goals,
                    "study_styles": shared_styles,
                    "shared_days": shared_days,
                    "shared_times": shared_times,
                },
            })

            # Mark members as used
            used_in_group.update(member_ids)

    # Sort groups by average score
    found_groups.sort(key=lambda g: g["avg_score"], reverse=True)
    return found_groups


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _find_common_values(students: list[dict], field: str) -> list[str]:
    """Find values shared by ALL students for a scalar field."""
    if not students:
        return []
    first_val = students[0].get(field, "")
    if all(s.get(field, "") == first_val for s in students):
        return [first_val]
    return []


def _find_common_list_values(students: list[dict], field: str) -> list[str]:
    """Find values present in ALL students' list fields."""
    if not students:
        return []
    common = set(students[0].get(field, []))
    for student in students[1:]:
        common &= set(student.get(field, []))
    return sorted(common)
