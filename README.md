# ResumeAI — Enterprise SaaS Resume Screening & Candidate Q&A Assistant

ResumeAI is a production-grade AI-powered resume screening, semantic ranking, and recruitment intelligence portal. Built for HR teams and technical recruiters, the system automates resume evaluations, provides interactive candidate chat interfaces using LLMs, and maps skill gap statistics across applicants.

---

## 🚀 Key Product Features

### 1. Recruitment Intelligence Dashboard
- **Cumulative Session Tracking:** Displays cumulative rankings, average scores, and candidate statistics across multiple batch screening uploads without losing session history.
- **Dynamic Similarity Slider:** A real-time filter threshold control allowing recruiters to filter out lower-tier candidates instantly.
- **Top Match Analytics:** High-level metrics showing the Total Screened, Top Fit Score, and a Fit Distribution (High / Med / Low) count based on customizable benchmarks.

### 2. Candidate Analysis slide-out Panel
- **Smart Tech Skill Matching:** Zero-dependency lexical analysis matching required skills dynamically from the job description.
- **Robust Synonym & Alias Resolution:** Prevents false negatives by mapping abbreviations and alternates (e.g., `JS` / `Java Script` -> `JavaScript`, `K8s` -> `Kubernetes`, `ML` -> `Machine Learning`).
- **Live PDF Document Viewer:** Embeds a secure, native iframe viewer displaying the uploaded PDF directly alongside the assessment checklist.
- **Resume AI Chat Assistant:** Interactive Q&A console powered by the latest **Google Gemini 3.5 Flash** model with full context-aware multi-turn conversation tracking in Flask sessions, quick-suggestion chips, and an offline fallback parser with ordinal/quantity filters.

### 3. Recruitment Analytics & Reporting
- **Talent Gap Deficit Analysis:** Automatically computes missing skill frequencies across candidates and renders a real-time progress bar chart highlighting skills most critical to source.
- **Skill Match Matrix:** A visual table highlighting skill match alignment (Found vs Missing) for the top 5 candidates.
- **CSV Data Export:** Recruiter tool to download ranking lists, similarity metrics, and missing skill reports as a standard CSV format.

### 4. Enterprise SaaS Security
- **Secure Authentication:** User login and signup pipelines backed by a SQLite database (`database.db`) with secure password hashing (`scrypt`).
- **Workspace Isolation:** Ensures candidates uploaded by one recruiter are strictly isolated from other recruiters' sessions using secure folder path resolution on disk.

---

## 🛠️ Architecture: Lexical TF-IDF vs. Neural SBERT

The backend supports two distinct matching pipelines:
1. **Core Lexical Matching (TF-IDF + Cosine Similarity):** Fast, lexical overlap matcher capturing word counts and bigrams (`ngram_range=(1,2)`) with sublinear term-frequency scaling.
2. **Deep Learning Semantic Matching (SBERT):** Upgrade path located in `ranker_advanced.py`. Uses `SentenceTransformer('all-MiniLM-L6-v2')` to embed resumes into a dense 384-dimensional vector space, capturing context and synonyms (e.g. "PostgreSQL" vs. "SQL database").

### Architectural Comparison Matrix

| Feature | TF-IDF (Lexical) | SBERT (Semantic Deep Learning) |
| :--- | :--- | :--- |
| **Core Mechanism** | Sparse bag-of-words / bigram counting | Dense neural text representations |
| **Context Awareness** | None (evaluates exact term count) | High (evaluates self-attention layers) |
| **Synonym Matching** | Strict (requires exact spelling/aliases) | Semantic (associates similar meanings) |
| **Execution Speed** | Extremely fast (milliseconds) | Slower (requires neural network forward pass) |
| **Hardware Requirements**| Low (CPU-bound) | High (CPU/GPU-bound) |

---

## 📦 Project Directory Structure

```text
├── app.py                # Flask main SaaS router and secure API controllers
├── preprocess.py         # Advanced text normalizer, skill matcher & Q&A parser
├── ranker.py             # Core TF-IDF ranking and matching calculations
├── ranker_advanced.py    # Deep Learning SBERT semantic model and benchmarks
├── extractor.py          # Secure PDF text extraction utility
├── database.db           # SQLite database for authentication and sessions
├── requirements.txt      # Python dependencies list
├── setup_nltk.py         # Automated NLTK database initializer script
├── test_ranker.py        # Automated test suite for correctness and edge cases
├── resumes_temp/         # Directory containing sample PDF resumes for verification
├── static/               # CSS and frontend assets
├── templates/            # HTML structural pages (landing, login, signup, dashboard)
└── uploads/              # Recruiter-isolated directory uploads (generated dynamically)
```

---

## ⚙️ Setup & Local Installation

### 1. Prerequisite Installations
Ensure you have Python 3.10+ installed on your machine.

### 2. Configure Virtual Environment
```bash
# Create environment
python -m venv venv

# Activate on Windows (cmd/PowerShell)
.\venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

### 3. Install Package Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize NLTK Database
```bash
python setup_nltk.py
```

### 5. Setup Environment File (`.env`)
Create a `.env` file in the root directory and configure:
```env
SECRET_KEY=dev_secret_key_12345
FLASK_APP=app.py
FLASK_ENV=development

# Gemini AI Configurations
GEMINI_API_KEY=your_google_ai_studio_api_key
GEMINI_MODEL=gemini-3.5-flash
```

---

## 🚀 Running the Application

### 1. Launch Web Server Locally
```bash
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

### 2. Run Automated Verification Tests
```bash
python test_ranker.py
```

### 3. Run TF-IDF vs. SBERT Benchmark Comparison
To measure SBERT deep learning execution speed against standard lexical metrics:
```bash
pip install sentence-transformers
python ranker_advanced.py
```

---

## 🔐 Credentials for Testing
- **Test Username:** `testuser_new`
- **Test Password:** `Password123`
- **Preloaded Resumes:** `candidate_alex.pdf` and `candidate_sarah.pdf` are already pre-seeded in the database for `testuser_new` to bypass local sandbox file-upload restrictions.
