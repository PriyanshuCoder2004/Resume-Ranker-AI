import os
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Constant list of 30 common tech skills for keyword matching
TECH_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "SQL", "HTML", "CSS",
    "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask", "Spring Boot",
    "Machine Learning", "Deep Learning", "Data Science", "Artificial Intelligence",
    "TensorFlow", "PyTorch", "AWS", "Docker", "Kubernetes", "Git", "Linux",
    "MongoDB", "PostgreSQL"
]

# Comprehensive list of standard skills for dynamic fallback (lowercase)
COMMON_TECH_SKILLS = {
    # Languages
    "python", "java", "c++", "c#", "c", "go", "golang", "rust", "swift", "kotlin", 
    "php", "ruby", "perl", "r", "scala", "dart", "haskell", "julia", "shell", "bash", 
    "html", "css", "sass", "less", "sql", "nosql", "graphql", "javascript", "typescript",
    # Frontend
    "react", "react.js", "react native", "angular", "angularjs", "vue", "vue.js", 
    "svelte", "next.js", "nuxt.js", "jquery", "bootstrap", "tailwind", "tailwindcss",
    "redux", "graphql",
    # Backend
    "node.js", "express", "express.js", "nestjs", "spring", "spring boot", "django", 
    "flask", "fastapi", "laravel", "symfony", "ruby on rails", "rails", "asp.net",
    # Databases & Cache
    "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis", "cassandra", 
    "dynamodb", "mariadb", "oracle", "firebase", "firestore", "elasticsearch", "neo4j",
    # Cloud & DevOps
    "aws", "gcp", "google cloud", "azure", "docker", "kubernetes", "k8s", "terraform", 
    "ansible", "jenkins", "circleci", "github actions", "ci/cd", "git", "github", "gitlab", 
    "linux", "unix", "nginx", "apache", "web3", "solidity", "hardhat", "truffle", "ethereum",
    "kafka", "spark", "hadoop", "tensorflow", "pytorch", "keras", "scikit-learn",
    "machine learning", "deep learning", "data science", "artificial intelligence",
    "data structures", "software engineering"
}

# Non-technical words to filter out if they are capitalized
NON_TECH_WORDS = {
    "job", "title", "developer", "engineer", "senior", "junior", "lead", "experience",
    "responsibilities", "requirements", "tools", "years", "degree", "bachelor", "master",
    "phd", "computer", "science", "engineering", "related", "field", "professional",
    "strong", "proficiency", "understanding", "ability", "work", "team", "teams",
    "collaborate", "design", "develop", "maintain", "write", "clean", "code", "efficient",
    "troubleshoot", "debug", "upgrade", "existing", "systems", "applications", "software",
    "development", "project", "projects", "management", "technical", "skills", "required",
    "plus", "preferred", "knowledge", "solid", "excellent", "communication", "written", 
    "verbal", "role", "overview", "seeking", "build", "create", "highly", "detail", 
    "oriented", "self", "motivated", "fast", "paced", "environment", "deliver", "high", 
    "quality", "solutions", "industry", "best", "practices", "designing", "implementing",
    "scalable", "robust", "services", "apis", "integration", "databases", "cloud", "deployment",
    "pipelines", "infrastructure", "continuous", "delivery", "version", "control", "collaborating", 
    "cross", "functional", "define", "ship", "new", "features", "troubleshooting", "debugging",
    "upgrading", "various", "platforms", "technologies", "innovative", "products", "product", 
    "managers", "designers", "other", "engineers", "adhere", "coding", "standards", "conduct", 
    "reviews", "participate", "architecture", "discussions", "ensure", "security", "reliability", 
    "performance", "candidate", "must", "have", "proven", "track", "record", "solving", "complex",
    "problems", "analytical", "thinking", "attention", "willingness", "learn", "adapt", "position", 
    "offers", "competitive", "salary", "benefits", "opportunity", "grow", "career", "dynamic", 
    "organization", "we", "you", "looking", "who", "expertise", "smart", "contracts", "mobile", 
    "apps", "using", "required", "deep", "pipeline", "pipelines", "test", "testing", "quality",
    "assurance", "user", "interface", "experience", "preferred", "degree", "bachelors", "masters",
    "key", "keys"
}

ENGLISH_STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
    "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", 
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", 
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", 
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", 
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
}

def extract_required_skills(jd_text):
    """
    Dynamically extracts technical skills and requirements from a Job Description (JD).
    Uses a combination of a comprehensive pre-defined tech skills database (100+ items)
    and POS-like casing rules (filtering out common English stopwords and non-tech terms).
    No external NLP downloads required (zero-dependency).
    """
    if not jd_text:
        return []
        
    found_skills = set()
    jd_lower = jd_text.lower()
    
    # 1. Match against our comprehensive technology list (case-insensitive) using full skill names
    # This correctly preserves multi-word skills like "Machine Learning", "Data Science", "Spring Boot", etc.
    for skill in COMMON_TECH_SKILLS:
        pattern = r""
        if re.match(r'^\w', skill):
            pattern += r'\b'
        pattern += re.escape(skill)
        if re.search(r'\w$', skill):
            pattern += r'\b'
            
        if re.search(pattern, jd_lower):
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                found_skills.add(match.group(0))
            else:
                found_skills.add(skill.title() if len(skill) > 3 else skill.upper())
                
    # 2. Extract capitalized words (candidate custom skills)
    jd_clean = re.sub(r'[^a-zA-Z0-9+#\-]', ' ', jd_text)
    words = jd_clean.split()
    
    for word in words:
        if len(word) >= 2 and word[0].isupper():
            word_lower = word.lower()
            if word_lower not in ENGLISH_STOPWORDS and word_lower not in NON_TECH_WORDS:
                # Check if this word is already part of a multi-word skill we found
                is_subpart = False
                for matched_skill in found_skills:
                    if len(matched_skill.split()) > 1 and word_lower in matched_skill.lower().split():
                        is_subpart = True
                        break
                if not is_subpart:
                    found_skills.add(word)
                    
    # Normalize naming casing
    normalized = {}
    for skill in found_skills:
        skill_lower = skill.lower()
        if skill_lower not in normalized or (skill[0].isupper() and not normalized[skill_lower][0].isupper()):
            normalized[skill_lower] = skill
            
    # Return sorted list of extracted skills
    return sorted(list(normalized.values()))

def preprocess(text):
    """
    Cleans and tokenizes text for NLP tasks.
    
    Processing Steps:
    1. Converts text to lowercase.
    2. Removes HTTP/HTTPS links (URLs).
    3. Removes email addresses.
    4. Removes phone numbers.
    5. Removes special characters/punctuation (keeps letters, numbers, spaces).
    6. Removes extra whitespaces and newlines.
    7. Tokenizes text into words.
    8. Removes NLTK English stopwords.
    9. Filters out words shorter than 2 characters.
    10. Joins tokens back into a single clean string.
    
    Args:
        text (str): The raw input text.
        
    Returns:
        str: The preprocessed and cleaned text.
    """
    if not text:
        return ""

    # 1. Lowercase conversion
    text = text.lower()

    # 2. Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)

    # 3. Remove emails
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', ' ', text)

    # 4. Remove phone numbers (handles various formats like +1-234-567-8900, (123) 456-7890, etc.)
    text = re.sub(r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b', ' ', text)
    text = re.sub(r'\+?\d[\d -]{7,15}\d', ' ', text)

    # 5. Remove special characters and punctuation (keep letters, numbers, spaces)
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    # 6. Normalize whitespaces (replaces multiple spaces/newlines with a single space)
    text = re.sub(r'\s+', ' ', text).strip()

    # 7. Tokenize
    try:
        tokens = word_tokenize(text)
    except Exception as e:
        # Fallback if NLTK tokenization encounters an issue
        tokens = text.split()

    # 8 & 9. Remove NLTK English stopwords and tokens shorter than 2 characters
    try:
        stop_words = set(stopwords.words('english'))
    except Exception:
        stop_words = set()

    filtered_tokens = [t for t in tokens if t not in stop_words and len(t) >= 2]

    # 10. Join back into a clean string
    return " ".join(filtered_tokens)

def extract_skills(text, skill_list):
    """
    Extracts detected and missing skills from the input text case-insensitively,
    supporting aliases and synonyms (e.g. 'JS' for 'JavaScript', 'K8s' for 'Kubernetes').
    
    Args:
        text (str): The raw or cleaned resume text.
        skill_list (list): A list of skill keywords to search for.
        
    Returns:
        dict: A dictionary containing two lists:
            - "found": List of skills detected in the text.
            - "missing": List of skills not detected.
    """
    found = []
    missing = []
    
    if not text:
        return {"found": [], "missing": list(skill_list)}
        
    text_lower = text.lower()
    
    # Synonyms mapping for tech skills
    SKILL_ALIASES = {
        "javascript": ["javascript", "js", "java script", "ecmascript", "es6"],
        "typescript": ["typescript", "ts", "type script"],
        "react": ["react", "reactjs", "react.js", "react js"],
        "angular": ["angular", "angularjs", "angular.js", "angular js"],
        "vue.js": ["vue", "vuejs", "vue.js", "vue js"],
        "node.js": ["node", "nodejs", "node.js", "node js"],
        "express": ["express", "expressjs", "express.js", "express js"],
        "django": ["django", "django framework"],
        "flask": ["flask", "flask framework"],
        "spring boot": ["spring boot", "spring", "springboot"],
        "machine learning": ["machine learning", "ml", "machinelearning"],
        "deep learning": ["deep learning", "dl", "deeplearning"],
        "data science": ["data science", "datascience"],
        "artificial intelligence": ["artificial intelligence", "ai", "artificialintelligence"],
        "aws": ["aws", "amazon web services", "amazon cloud"],
        "docker": ["docker", "docker.io", "docker container"],
        "kubernetes": ["kubernetes", "k8s"],
        "git": ["git", "github", "gitlab", "version control"],
        "mongodb": ["mongodb", "mongo", "mongo db"],
        "postgresql": ["postgresql", "postgres", "postgre sql", "postgres sql"],
        "c++": ["c++", "cpp"],
        "c#": ["c#", "c-sharp", "csharp"],
        "data structures": ["data structures", "datastructures"],
        "software engineering": ["software engineering", "software development", "software design"]
    }
    
    for skill in skill_list:
        skill_lower = skill.lower()
        
        # Get aliases for this skill, defaulting to the skill name itself
        aliases = SKILL_ALIASES.get(skill_lower, [skill_lower])
        
        has_match = False
        for alias in aliases:
            # Escape alias for regex safety
            escaped_alias = re.escape(alias)
            
            # Construct pattern using word boundaries only where appropriate
            pattern = r""
            if re.match(r'^\w', alias):
                pattern += r'\b'
            pattern += escaped_alias
            if re.search(r'\w$', alias):
                pattern += r'\b'
                
            if re.search(pattern, text_lower):
                has_match = True
                break
                
        if has_match:
            found.append(skill)
        else:
            missing.append(skill)
            
    return {
        "found": found,
        "missing": missing
    }

# Attempt to configure Gemini AI
HAS_GEMINI = False
try:
    import google.generativeai as genai
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        HAS_GEMINI = True
except ImportError:
    pass

def call_gemini_api(resume_text, question, chat_history=None):
    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=f"You are an expert technical recruiter and AI assistant. Answer the user's questions about the candidate based ONLY on the provided resume text. If the information is not present in the resume, clearly state that it is not mentioned. Keep your response concise, professional, and format it nicely in structured Markdown with bullet points and bold text.\n\nCandidate Resume:\n{resume_text}"
        )
        
        formatted_history = []
        if chat_history:
            for msg in chat_history:
                formatted_history.append({
                    'role': 'user' if msg['role'] == 'user' else 'model',
                    'parts': [msg['content']]
                })
                
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(question)
        return response.text.strip()
    except Exception as e:
        # Fallback to local rule-based if API call fails
        print(f"[Gemini Error] {e}")
        return None

def parse_resume_sections(resume_text):
    """
    Parses the raw resume text into logical sections based on headers.
    """
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    sections = {
        "summary": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "general": []
    }
    
    current_section = "general"
    
    for line in lines:
        line_lower = line.lower()
        # Detect section header
        if any(h in line_lower for h in ["summary", "profile", "about me", "professional summary"]):
            current_section = "summary"
            continue
        elif any(h in line_lower for h in ["skills", "technical skills", "core competencies", "technologies", "expertise"]):
            current_section = "skills"
            continue
        elif any(h in line_lower for h in ["experience", "employment", "history", "work history", "career", "professional experience"]):
            current_section = "experience"
            continue
        elif any(h in line_lower for h in ["projects", "personal projects", "academic projects", "key projects"]):
            current_section = "projects"
            continue
        elif any(h in line_lower for h in ["education", "academic", "university", "credentials", "degrees"]):
            current_section = "education"
            continue
            
        sections[current_section].append(line)
        
    return sections

def answer_resume_question(resume_text, question, chat_history=None):
    """
    Simulates a smart AI recruiter chat assistant.
    If GEMINI_API_KEY is configured in the environment, it uses Google Gemini AI.
    Otherwise, it falls back to a highly accurate rule-based semantic parser.
    """
    # 1. Attempt Gemini AI if key is set
    gemini_key = os.getenv("GEMINI_API_KEY")
    if HAS_GEMINI and gemini_key:
        gemini_ans = call_gemini_api(resume_text, question, chat_history)
        if gemini_ans:
            return gemini_ans

    # 2. Local Fallback Q&A Engine
    if not resume_text or not question:
        return "I'm sorry, I couldn't access the candidate's resume or your question. Please try again."

    q_lower = question.lower().strip()
    sections = parse_resume_sections(resume_text)
    
    # Extract candidate name if available on the first line
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    candidate_name = lines[0] if lines else "the candidate"
    
    # Detect intent
    # A. Profile Summary
    if any(k in q_lower for k in ["summarize", "summary", "overview", "profile", "who is", "about"]):
        summary_text = " ".join(sections["summary"]) if sections["summary"] else ""
        if not summary_text:
            # Fallback: first few lines
            summary_text = " ".join(lines[1:5]) if len(lines) > 1 else ""
        if not summary_text:
            summary_text = "Experienced software engineering candidate with a strong technical background."
            
        return f"### Candidate Profile Summary: **{candidate_name}**\n\n" \
               f"Here is a summary of the candidate's profile based on their resume:\n\n" \
               f"> {summary_text}\n\n" \
               f"**Key Strengths Identified:**\n" \
               f"- Matches relevant technical role profiles.\n" \
               f"- Documented experience and skills in development frameworks."

    # B. Technical Stack / Skills
    elif any(k in q_lower for k in ["skills", "tech stack", "languages", "frameworks", "technologies", "know"]):
        skills_text = ", ".join(sections["skills"]) if sections["skills"] else ""
        if not skills_text:
            # Fallback: scan for COMMON_TECH_SKILLS in the resume
            matched_skills = []
            for skill in COMMON_TECH_SKILLS:
                if re.search(r'\b' + re.escape(skill) + r'\b', resume_text.lower()):
                    matched_skills.append(skill.upper() if len(skill) <= 3 else skill.title())
            skills_text = ", ".join(sorted(list(set(matched_skills))))
        if not skills_text:
            skills_text = "General software development skills."
            
        return f"### Technical Skills & Stack: **{candidate_name}**\n\n" \
               f"Based on the resume, the candidate possesses the following technical competencies:\n\n" \
               f"- **Core Stack & Skills:** {skills_text}\n" \
               f"- **Skill Coverage:** Prepared for design, deployment, database manipulation, and version control procedures."

    # C. Projects
    elif any(k in q_lower for k in ["projects", "project", "portfolio", "built", "developed"]):
        project_lines = sections["projects"]
        if not project_lines:
            # Try to search general lines mentioning "project" or "built"
            project_lines = [l for l in lines if any(p in l.lower() for p in ["project", "built", "developed", "implemented", "designed", "created"])]
            
        if not project_lines:
            return f"### Projects & Portfolio: **{candidate_name}**\n\n" \
                   f"The candidate's resume does not explicitly list distinct project titles, but documents software engineering implementations within their work experience."
                   
        project_bullets = "\n".join([f"- {l}" for l in project_lines[:6]])
        return f"### Key Projects & Technical Works: **{candidate_name}**\n\n" \
               f"Here are the key projects and implementations mentioned in the candidate's profile:\n\n" \
               f"{project_bullets}"

    # D. Experience / History
    elif any(k in q_lower for k in ["experience", "employment", "history", "work", "job", "career", "role"]):
        exp_lines = sections["experience"]
        if not exp_lines:
            exp_lines = [l for l in lines if any(e in l.lower() for e in ["engineer", "developer", "lead", "manager", "intern", "coordinator"])]
            
        if not exp_lines:
            return f"### Work Experience: **{candidate_name}**\n\n" \
                   f"The candidate's resume lists software engineering practices and background, but job history sections could not be isolated."
                   
        exp_bullets = "\n".join([f"- {l}" for l in exp_lines[:6]])
        return f"### Professional Work Experience: **{candidate_name}**\n\n" \
               f"Here is a timeline and log of the candidate's work history:\n\n" \
               f"{exp_bullets}"

    # E. Specific Technology queries (e.g. "Do they know Docker?")
    else:
        # Find which tech terms from COMMON_TECH_SKILLS are in the question
        query_tech = []
        for skill in COMMON_TECH_SKILLS:
            if re.search(r'\b' + re.escape(skill) + r'\b', q_lower):
                query_tech.append(skill)
                
        if not query_tech:
            # General keyword search fallback
            matching_lines = []
            words = q_lower.split()
            search_words = [w for w in words if w not in ENGLISH_STOPWORDS and len(w) > 2]
            
            for line in lines:
                if any(w in line.lower() for w in search_words):
                    matching_lines.append(line)
            
            if matching_lines:
                bullets = "\n".join([f"- *... {l} ...*" for l in matching_lines[:3]])
                return f"### Search Results: **{candidate_name}**\n\n" \
                       f"I found some matching context in the candidate's resume:\n\n" \
                       f"{bullets}"
            else:
                return f"### Assistant Reply\n\n" \
                       f"I searched the resume of **{candidate_name}** for details regarding your query, but could not find direct references. Let me know if you would like me to check their general profile summary or technical stack!"

        # Specific tech queries
        found_matches = []
        for tech in query_tech:
            pattern = r""
            if re.match(r'^\w', tech):
                pattern += r'\b'
            pattern += re.escape(tech)
            if re.search(r'\w$', tech):
                pattern += r'\b'
                
            # Search resume for this tech
            matches = [line for line in lines if re.search(pattern, line.lower())]
            if matches:
                found_matches.extend(matches)
                
        unique_matches = []
        for item in found_matches:
            if item not in unique_matches:
                unique_matches.append(item)
                
        tech_title = ", ".join([t.upper() if len(t) <= 3 else t.title() for t in query_tech])
        if unique_matches:
            bullets = "\n".join([f"- {l}" for l in unique_matches[:4]])
            return f"### Technical Match: **{tech_title}**\n\n" \
                   f"Yes, **{candidate_name}** has references to **{tech_title}** in their resume:\n\n" \
                   f"{bullets}"
        else:
            return f"### Technical Match: **{tech_title}**\n\n" \
                   f"Based on the resume text, **{candidate_name}** does not have explicit references to **{tech_title}**. Let me know if you would like me to check for other technical skills!"

if __name__ == "__main__":
    print("--- Testing preprocess.py Module ---")
    
    # Sample Mock Resume Text
    sample_resume = """
    Jane Smith
    Senior Software Developer
    Email: jane.smith@example.com | Phone: +1 (555) 019-2834 | Web: https://janesmith.dev
    
    Professional Summary:
    Detail-oriented software development engineer with 5+ years of experience.
    Proficient in building backend applications using Python, Flask, and Django.
    Hands-on experience with Docker containerization, Kubernetes orchestration, and AWS cloud.
    Strong foundation in database queries using SQL and PostgreSQL.
    Also worked on machine learning and basic natural language processing algorithms.
    
    Core Skills:
    Python, SQL, React, Docker, Kubernetes, AWS, Machine Learning, Git.
    """
    
    print("\n--- Original Resume Snippet ---")
    print(sample_resume[:250] + "...")
    
    print("\n--- Running Preprocessing ---")
    cleaned_text = preprocess(sample_resume)
    print("Preprocessed Output:")
    print(cleaned_text[:300] + "...")
    
    print("\n--- Running Skill Extraction ---")
    extracted = extract_skills(sample_resume, TECH_SKILLS)
    print(f"Found Skills ({len(extracted['found'])}): {extracted['found']}")
    print(f"Missing Skills ({len(extracted['missing'])}): {extracted['missing']}")
