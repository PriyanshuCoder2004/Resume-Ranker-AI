import json
from ranker import rank_resumes, get_skill_breakdown

def run_tests():
    # 1. Sample Job Description
    sample_jd = """
    We are seeking a Software Engineer.
    Key skills: Python, Machine Learning, SQL, Data Structures, Git, AWS.
    You will build machine learning models, perform database queries using SQL,
    implement core data structures, deploy to AWS cloud, and collaborate via Git.
    """

    # 2. Mock Resumes
    resume_perfect = """
    Senior Software Engineer with extensive experience in Python programming and Machine Learning.
    Expert in SQL databases, SQL querying, and implementation of complex Data Structures.
    Frequently deploy and manage cloud systems in AWS. Manage version control systems using Git.
    Strong understanding of core computer science fundamentals and data structures.
    """

    resume_good = """
    Backend Developer. Strong experience in Python programming and SQL.
    Managed development environments on AWS and handled version control using Git.
    Focused on writing scalable code and database optimization.
    """

    resume_medium = """
    Junior Developer. Proficient in Python.
    Have written simple scripts and managed a basic PostgreSQL database using SQL.
    Interested in learning more about Git and AWS.
    """

    resume_poor = """
    Technical Project Coordinator. Experienced in scrum methodologies.
    Coordinate with developers who use Git for tracking progress.
    No direct coding experience, but familiar with software lifecycles.
    """

    resume_unrelated = """
    Culinary Chef and kitchen supervisor.
    Experienced in French cooking, food preparation, menu planning,
    and managing restaurant kitchen staff. Certified in food safety.
    """

    resume_dict = {
        "resume_perfect.pdf": resume_perfect,
        "resume_good.pdf": resume_good,
        "resume_medium.pdf": resume_medium,
        "resume_poor.pdf": resume_poor,
        "resume_unrelated.pdf": resume_unrelated
    }

    print("==================================================")
    print("      STARTING RESUME RANKER SYSTEM TESTS         ")
    print("==================================================")

    # ==========================================================================
    # TEST 1: Similarity Rankings & Monotonicity
    # ==========================================================================
    print("\n[TEST 1] Testing Rank Calculations & Order...")
    
    rankings = rank_resumes(sample_jd, resume_dict)
    
    # Store ranking mapping for easy lookup
    rank_map = {item["name"]: item for item in rankings}
    
    # Assertions
    try:
        assert len(rankings) == 5, f"Expected 5 ranked resumes, got {len(rankings)}"
        
        # Perfect resume should rank #1
        assert rankings[0]["name"] == "resume_perfect.pdf", f"Expected resume_perfect to rank #1, got {rankings[0]['name']}"
        
        # Unrelated resume should rank #5
        assert rankings[4]["name"] == "resume_unrelated.pdf", f"Expected resume_unrelated to rank #5, got {rankings[4]['name']}"
        
        # Check monotonic decreasing scores from rank 1 to 5
        for i in range(len(rankings) - 1):
            assert rankings[i]["score"] >= rankings[i+1]["score"], \
                f"Score ordering error: Rank {i+1} ({rankings[i]['score']}%) is lower than Rank {i+2} ({rankings[i+1]['score']}%)"
                
        test_1_status = "PASS"
    except AssertionError as e:
        test_1_status = f"FAIL ({str(e)})"

    # Print Formatted Results Table
    print("\nRankings Output Table:")
    print(f"{'Rank':<6} | {'Candidate File':<22} | {'Similarity Score':<16} | {'Status':<6}")
    print("-" * 59)
    for idx, item in enumerate(rankings, start=1):
        status = "OK"
        if idx == 1 and item["name"] != "resume_perfect.pdf": status = "FAIL"
        elif idx == 5 and item["name"] != "resume_unrelated.pdf": status = "FAIL"
        
        print(f"{item['rank']:<6} | {item['name']:<22} | {item['score']:>14}% | {status:<6}")
    
    print(f"\n---> TEST 1 Status: {test_1_status}")

    # ==========================================================================
    # TEST 2: Skill Extraction & Match Scoring
    # ==========================================================================
    print("\n[TEST 2] Testing Skill Extraction Breakdown...")
    
    skills_breakdown = get_skill_breakdown(sample_jd, resume_dict)
    
    try:
        # Perfect resume should match all or almost all required skills
        perfect_skills = skills_breakdown["resume_perfect.pdf"]
        assert perfect_skills["skill_score"] >= 80.0, f"Perfect resume skill score too low: {perfect_skills['skill_score']}%"
        
        # Unrelated resume should match 0 skills
        unrelated_skills = skills_breakdown["resume_unrelated.pdf"]
        assert unrelated_skills["skill_score"] == 0.0, f"Unrelated resume matched skills: {unrelated_skills['found']}"
        
        # Check that scores follow expected order
        assert skills_breakdown["resume_perfect.pdf"]["skill_score"] >= skills_breakdown["resume_good.pdf"]["skill_score"]
        assert skills_breakdown["resume_good.pdf"]["skill_score"] >= skills_breakdown["resume_medium.pdf"]["skill_score"]
        assert skills_breakdown["resume_medium.pdf"]["skill_score"] >= skills_breakdown["resume_poor.pdf"]["skill_score"]
        assert skills_breakdown["resume_poor.pdf"]["skill_score"] >= skills_breakdown["resume_unrelated.pdf"]["skill_score"]
        
        test_2_status = "PASS"
    except AssertionError as e:
        test_2_status = f"FAIL ({str(e)})"
        
    print("\nSkills Match Table:")
    print(f"{'Candidate File':<22} | {'Skill Score':<12} | {'Found Skills'}")
    print("-" * 65)
    for name, info in skills_breakdown.items():
        print(f"{name:<22} | {info['skill_score']:>10}% | {info['found']}")
        
    print(f"\n---> TEST 2 Status: {test_2_status}")

    # ==========================================================================
    # TEST 3: Edge Cases (Robustness / Non-crashing)
    # ==========================================================================
    print("\n[TEST 3] Testing System Robustness on Edge Cases...")
    
    edge_cases = {
        "empty_resume.pdf": "",
        "special_chars.pdf": "!@#$ %^&* ()_+",
        "single_word.pdf": "Python"
    }
    
    try:
        # Run ranker on edge cases against sample JD
        edge_rankings = rank_resumes(sample_jd, edge_cases)
        edge_skills = get_skill_breakdown(sample_jd, edge_cases)
        
        # Verify that three entries are returned without raising exceptions
        assert len(edge_rankings) == 3, f"Expected 3 edge cases rankings, got {len(edge_rankings)}"
        assert len(edge_skills) == 3, f"Expected 3 edge cases skill summaries, got {len(edge_skills)}"
        
        # Empty and special characters should score 0 similarity
        empty_score = next(item["score"] for item in edge_rankings if item["name"] == "empty_resume.pdf")
        special_score = next(item["score"] for item in edge_rankings if item["name"] == "special_chars.pdf")
        
        assert empty_score == 0.0, f"Expected empty resume similarity 0.0, got {empty_score}"
        assert special_score == 0.0, f"Expected special char resume similarity 0.0, got {special_score}"
        
        # Single word Python should find "Python" in skills
        assert "Python" in edge_skills["single_word.pdf"]["found"], "Expected Python skill to be extracted"
        assert len(edge_skills["single_word.pdf"]["found"]) == 1, "Expected only 1 skill found"
        
        test_3_status = "PASS"
    except AssertionError as e:
        test_3_status = f"FAIL ({str(e)})"
    except Exception as e:
        test_3_status = f"FAIL (Crashed with exception: {str(e)})"
        
    print(f"\n---> TEST 3 Status: {test_3_status}")
    print("==================================================")
    
    # Return overall status
    if "FAIL" in [test_1_status, test_2_status, test_3_status]:
        print("OVERALL TESTING RESULT: FAILED")
        return False
    else:
        print("OVERALL TESTING RESULT: ALL PASSED")
        return True

if __name__ == "__main__":
    run_tests()
