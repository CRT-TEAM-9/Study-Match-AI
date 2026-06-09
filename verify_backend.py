import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from database.db_helper import load_students, find_student_by_id
from backend.matching_engine import calculate_compatibility, find_matches, find_study_groups

def test_db():
    print("--- Testing Database Helper ---")
    students = load_students()
    print(f"Loaded {len(students)} students from database.")
    if not students:
        print("❌ Error: No students found in database!")
        return False
    
    # Try finding STU001
    stu1 = find_student_by_id("STU001")
    if stu1:
        print(f"✅ Found STU001: {stu1['name']} ({stu1['branch']})")
    else:
        print("❌ Error: STU001 not found!")
        return False
    return True

def test_matching():
    print("\n--- Testing Matching Engine ---")
    students = load_students()
    if not students:
        return False
        
    stu1 = students[0]
    print(f"Finding matches for: {stu1['name']}")
    
    matches = find_matches(stu1, students, top_n=3, threshold=30.0)
    print(f"Found {len(matches)} matches:")
    for i, match in enumerate(matches, 1):
        partner = match['partner']
        print(f"  {i}. {partner['name']} - Compatibility: {match['overall_score']}%")
        
    # Test groups
    groups = find_study_groups(students, min_size=3, threshold=40.0)
    print(f"Found {len(groups)} study groups:")
    for i, group in enumerate(groups, 1):
        members = ", ".join(m['name'] for m in group['members'])
        print(f"  Group {i} ({group['avg_score']}% avg compatibility): {members}")
        
    return True

if __name__ == "__main__":
    db_ok = test_db()
    matching_ok = test_matching()
    if db_ok and matching_ok:
        print("\n🎉 Backend modules verified successfully!")
    else:
        print("\n❌ Backend verification failed.")
