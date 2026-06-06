from preprocess import preprocess, extract_skills, TECH_SKILLS, extract_required_skills
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank_resumes(jd_text, resume_dict):
    """
    Ranks resumes against a job description based on TF-IDF cosine similarity.
    
    Args:
        jd_text (str): Job description text.
        resume_dict (dict): Dictionary mapping filename to resume text.
        
    Returns:
        list: Sorted list of dicts containing filename, similarity score, and rank.
              Example: [{"name": "resume.pdf", "score": 87.3, "rank": 1}, ...]
    """
    if not jd_text or not resume_dict:
        return []
        
    filenames = list(resume_dict.keys())
    
    # 1. Preprocess the Job Description
    cleaned_jd = preprocess(jd_text)
    
    # 2. Preprocess all resumes
    cleaned_resumes = []
    for filename in filenames:
        cleaned_resumes.append(preprocess(resume_dict[filename]))
        
    # 3. Combine JD and resumes to form the TF-IDF corpus
    corpus = [cleaned_jd] + cleaned_resumes
    
    try:
        # Use ngram_range=(1,2) to capture bigrams, sublinear TF scaling, and cap features at 5000
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Index 0 is the Job Description vector
        jd_vector = tfidf_matrix[0]
        # Index 1+ are the resumes vectors
        resumes_vectors = tfidf_matrix[1:]
        
        # Calculate Cosine Similarity between JD and all Resumes
        similarities = cosine_similarity(resumes_vectors, jd_vector).flatten()
        
        ranked_results = []
        for i, similarity in enumerate(similarities):
            # Convert similarity score to percentage and round to 1 decimal place
            percentage_score = round(float(similarity) * 100, 1)
            ranked_results.append({
                "name": filenames[i],
                "score": percentage_score
            })
            
        # Sort results by score in descending order
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Assign rank indices
        for rank_idx, result in enumerate(ranked_results, start=1):
            result["rank"] = rank_idx
            
        return ranked_results
        
    except Exception as e:
        print(f"[ERROR] Vectorization/Cosine Similarity calculation failed: {e}")
        # Safe fallback: return 0.0 scores if fitting fails
        return [{"name": name, "score": 0.0, "rank": idx} for idx, name in enumerate(filenames, start=1)]

def get_skill_breakdown(jd_text, resume_dict):
    """
    Extracts required tech skills automatically from the job description (JD),
    then parses each resume to find which skills are present and which are missing.
    Calculates a skill match percentage.
    
    Args:
        jd_text (str): Job description text.
        resume_dict (dict): Dictionary mapping filename to resume text.
        
    Returns:
        dict: Mapping of filename to found/missing skills and skill score.
              Example: {filename: {"found": [...], "missing": [...], "skill_score": 75.0}}
    """
    if not resume_dict:
        return {}
        
    # 1. Automatically detect required skills dynamically from the Job Description text
    required_skills = extract_required_skills(jd_text)
    
    # Fallback: If no tech skills are found/extracted from the JD, use the global list
    # so we still provide a meaningful match breakdown.
    if not required_skills:
        compare_skills = TECH_SKILLS
    else:
        compare_skills = required_skills
        
    breakdown = {}
    
    # 2. Extract matches for each resume
    for filename, resume_text in resume_dict.items():
        resume_analysis = extract_skills(resume_text, compare_skills)
        found = resume_analysis["found"]
        missing = resume_analysis["missing"]
        
        # Compute skill match score as a percentage
        total_req = len(compare_skills)
        skill_score = round((len(found) / total_req) * 100, 1) if total_req > 0 else 0.0
        
        breakdown[filename] = {
            "found": found,
            "missing": missing,
            "skill_score": skill_score
        }
        
    return breakdown

def generate_report(ranked_results, skill_breakdown):
    """
    Consolidates similarity rankings and skill breakdowns into a single list of dicts.
    
    Args:
        ranked_results (list): Output of rank_resumes.
        skill_breakdown (dict): Output of get_skill_breakdown.
        
    Returns:
        list: Consolidated list of detailed rankings sorted by rank.
    """
    consolidated_report = []
    
    for item in ranked_results:
        filename = item["name"]
        skills_info = skill_breakdown.get(filename, {
            "found": [],
            "missing": [],
            "skill_score": 0.0
        })
        
        consolidated_report.append({
            "rank": item["rank"],
            "name": filename,
            "similarity_score": item["score"],
            "skill_score": skills_info["skill_score"],
            "found_skills": skills_info["found"],
            "missing_skills": skills_info["missing"]
        })
        
    return consolidated_report

if __name__ == "__main__":
    # Test dataset for verification
    sample_jd = """
    We are seeking a Backend Developer.
    Must have experience with Python, SQL, and AWS.
    Experience with Docker, Kubernetes, and Machine Learning is a plus.
    We value version control using Git.
    """
    
    sample_resumes = {
        "candidate_john.pdf": "I am a Python developer with experience in SQL, Docker, AWS, and Git.",
        "candidate_sarah.pdf": "Expert developer skilled in Java, Spring Boot, NoSQL, Git and AWS Cloud. Familiar with Docker.",
        "candidate_alex.pdf": "Frontend expert. Proficient in HTML, CSS, JavaScript, and React. Basic knowledge of Python and Git."
    }
    
    print("--- Testing ranker.py Module ---")
    
    print("\n[STEP 1] Running rank_resumes...")
    rankings = rank_resumes(sample_jd, sample_resumes)
    print(rankings)
    
    print("\n[STEP 2] Running get_skill_breakdown...")
    skills_data = get_skill_breakdown(sample_jd, sample_resumes)
    for name, data in skills_data.items():
        print(f"\n- {name}:")
        print(f"  Skill Match Score: {data['skill_score']}%")
        print(f"  Found: {data['found']}")
        print(f"  Missing: {data['missing']}")
        
    print("\n[STEP 3] Generating Consolidated Report...")
    report = generate_report(rankings, skills_data)
    
    # Print clean JSON format report
    import json
    print(json.dumps(report, indent=2))
