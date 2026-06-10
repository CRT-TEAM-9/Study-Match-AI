# Nexus AI — Automated Test Results

Run at: 2026-06-10 20:12:12
Backend: http://localhost:5000

**Total: 22 | Pass: 22 | Fail: 0**

---

## Match Queries (10/10 passed)

| Test ID | User Message | Expected | Actual | Status |
|---|---|---|---|---|
| M1.1 | Aarav Sharma — find matches | At least one DBMS-strong student in top 3 matches (candidates: ['Priya Patel', ' | Got matches: ['Arjun Nair', 'Anjali Krishnan', 'Kavya Sharma'], scores: [80.0, 8 | PASS |
| M1.2 | Aarav Sharma — scores >= 30% | All returned match scores >= 30% | Scores: [80.0, 80.0, 72.5] | PASS |
| M2.1 | Sneha Reddy — find matches | At least one ML/Cloud-strong student in matches (candidates: ['Aarav Sharma', 'M | Got: ['Tanvi Singh', 'Aditya Rao', 'Aarav Sharma'] | PASS |
| M2.2 | Sneha Reddy — project work goal alignment | Project work students preferred (candidates: ['Aditya Rao', 'Tanvi Singh']) | Got: ['Tanvi Singh', 'Aditya Rao', 'Aarav Sharma'] | PASS |
| M3.1 | Vikram Joshi — find ECE matches | At least one Microprocessors/Embedded Systems-strong student (candidates: ['Roha | Got: ['Ravi Kumar', 'Rohan Mehta'] | PASS |
| M3.2 | Vikram Joshi — Ravi Kumar appears in top 3 | Ravi Kumar (strong in Micro/Embedded, competitive exam) appears in matches | Got: ['Ravi Kumar', 'Rohan Mehta'] | PASS |
| M4.1 | Harsha Reddy — find Python-strong matches | At least one Python-strong student in matches (candidates: ['Aarav Sharma', 'Roh | Got: ['Nisha Verma', 'Rohan Mehta', 'Suresh Babu'] | PASS |
| M4.2 | Harsha Reddy — scores reflect 1st year limited overlap | Scores should exist but may be lower (< 60%) due to limited subject pool | Top scores: [52.5, 45.0, 45.0] | PASS |
| M5.1 | Nisha Verma — niche civil subjects return low or no matches | No matches OR all match scores <= 60% (niche subject pool) | Matches: ['Harsha Reddy', 'Suresh Babu', 'Karan Singh'], Scores: [52.5, 50.5, 36 | PASS |
| M5.2 | Nisha Verma — no crash or error on low matches | API returns 200 with matches list (may be empty) | status=200, matches=3 | PASS |

## Edge Case (2/2 passed)

| Test ID | User Message | Expected | Actual | Status |
|---|---|---|---|---|
| E1 | Orbit Isolated profile found | Profile exists in database with niche Aerospace subjects | Found student_id=STU027 | PASS |
| E2 | Orbit Isolated — no high-compatibility matches returned | 0 matches above 30% threshold returned (unique niche subject area) | Matches: [], Scores: [] | PASS |

## Group Formation (2/2 passed)

| Test ID | User Message | Expected | Actual | Status |
|---|---|---|---|---|
| G1 | Aarav Sharma — study group containing 3+ members returned | At least one study group with 3+ members including Aarav Sharma | Groups found: 2, members: [['Aarav Sharma', 'Arjun Nair', 'Anjali Krishnan', 'Ka | PASS |
| G2 | Group card has avg_score >= 40%, 3+ members, shared days | avg_score >= 40, member_count >= 3, shared_days populated | avg_score=63.4, members=7, shared_days=['Friday', 'Monday', 'Wednesday'] | PASS |

## Consistency (8/8 passed)

| Test ID | User Message | Expected | Actual | Status |
|---|---|---|---|---|
| C1 | Bidirectional matching — A in B's list iff B in A's list | Score(Aarav→Priya) == Score(Priya→Aarav) | A→B=52.5, B→A=52.5 | PASS |
| C2 | Same study style scores 100% on style factor | study_style score = 100.0 when both students have style=discussion | style score=100.0 | PASS |
| C3 | Different goals score 0% on goal factor | goal_match score = 0.0 when exam prep vs research | goal score=0.0 | PASS |
| C4 | No schedule overlap → time_day_overlap score = 0% | time_day_overlap score = 0.0 when no shared times or days | time_day score=0.0 | PASS |
| C5 | Student is never matched with themselves | Aarav Sharma's student_id never appears in his own match results | self_excluded=True | PASS |
| C6 | Match results are sorted by score descending | Each match score >= the next match score | Scores: [80.0, 80.0, 72.5, 70.0, 57.5] | PASS |
| C7 | Complementary strengths weight = 40% | weight_pct=40 in breakdown | weight_pct=40 | PASS |
| C8 | Perfectly complementary students score 100% | overall_score = 100.0 | overall_score=100.0 | PASS |
