import os
import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Import custom processing modules
from extractor import extract_text_from_pdf
from ranker import rank_resumes, get_skill_breakdown
from preprocess import answer_resume_question

app = Flask(__name__)

# Flask Configurations
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_secret_key_12345")
UPLOAD_FOLDER = os.path.abspath("./uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16MB file upload limit

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'database.db'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Initialize DB on startup
init_db()

def allowed_file(filename):
    """Checks if the file extension is .pdf."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/', methods=['GET'])
def index():
    """Renders the main Landing Page."""
    return render_template('landing.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Renders the main upload and screening dashboard page (protected)."""
    if 'username' not in session:
        return redirect(url_for('login'))
    db = get_db()
    user = db.execute('SELECT username, email, created_at FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Renders user login page and handles authentication."""
    if 'username' in session:
        return redirect(url_for('dashboard'))
        
    error = None
    if request.method == 'POST':
        username_or_email = request.form['username'].strip()
        password = request.form['password']
        
        if not username_or_email or not password:
            error = 'Please enter both username/email and password.'
        else:
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username_or_email, username_or_email)).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid username/email or password.'
                
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Renders user registration page and handles signup."""
    if 'username' in session:
        return redirect(url_for('dashboard'))
        
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        
        if not username or not email or not password:
            error = 'All fields are required.'
        else:
            db = get_db()
            existing_user = db.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
            if existing_user:
                error = 'Username or Email is already registered.'
            else:
                try:
                    db.execute(
                        'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                        (username, email, generate_password_hash(password))
                    )
                    db.commit()
                    
                    # Log in automatically
                    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    error = f'Database error: {str(e)}'
                    
    return render_template('signup.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
    """Clears the session and logs the user out."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/health', methods=['GET'])
def health():
    """Simple health check endpoint for monitoring/deployment checks."""
    return jsonify({"status": "ok"}), 200

@app.route('/rank', methods=['POST'])
def rank():
    """
    Endpoint for uploading resumes and ranking them against a Job Description.
    Expects multipart/form-data:
      - 'jd': Text string of the job description.
      - 'resumes': List of PDF files.
    """
    # Protect Rank API
    if 'username' not in session:
        return jsonify({"success": False, "error": "Unauthorized session. Please log in."}), 401
        
    # 1. Validate Job Description field
    if 'jd' not in request.form:
        return jsonify({"success": False, "error": "Missing 'jd' text field in request."}), 400
        
    jd_text = request.form['jd'].strip()
    if not jd_text:
        return jsonify({"success": False, "error": "Job description cannot be empty."}), 400
        
    # 2. Validate Resume files field
    if 'resumes' not in request.files:
        return jsonify({"success": False, "error": "No resume files uploaded."}), 400
        
    uploaded_files = request.files.getlist('resumes')
    
    # Check if files list is empty or has a blank file object (no selection made)
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"success": False, "error": "No files selected for upload."}), 400

    user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    os.makedirs(user_upload_dir, exist_ok=True)
    
    saved_file_paths = []
    resume_dict = {}
    
    try:
        # 3. Process and temporarily save files in user-isolated directory, then extract text
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Check for filename collisions and generate a safe path
                save_path = os.path.join(user_upload_dir, filename)
                file.save(save_path)
                saved_file_paths.append(save_path)
                
                # Extract clean text from the PDF file
                extracted_text = extract_text_from_pdf(save_path)
                
                # Store text in dict with the filename as key
                resume_dict[filename] = extracted_text
            else:
                # Clean up uploaded files in case of format error
                for fp in saved_file_paths:
                    if os.path.exists(fp):
                        try:
                            os.remove(fp)
                        except:
                            pass
                return jsonify({
                    "success": False, 
                    "error": f"Invalid file format for '{file.filename}'. Only PDF files are allowed."
                }), 400

        if not resume_dict:
            return jsonify({"success": False, "error": "Failed to extract text from any of the uploaded resumes."}), 400
            
        # 4. Perform ML Ranking (similarity scoring)
        rankings = rank_resumes(jd_text, resume_dict)
        
        # 5. Extract matching and missing skills from the JD baseline
        skill_breakdown = get_skill_breakdown(jd_text, resume_dict)
        
        # 6. Return response in specified format
        return jsonify({
            "success": True,
            "results": rankings,
            "skill_breakdown": skill_breakdown
        }), 200
        
    except Exception as e:
        app.logger.error(f"[ERROR] Exception during rank request: {e}")
        # Clean up files uploaded during this failed request
        for fp in saved_file_paths:
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except:
                pass
        return jsonify({
            "success": False, 
            "error": f"An internal error occurred during processing: {str(e)}"
        }), 500

@app.route('/view-pdf/<filename>', methods=['GET'])
def view_pdf(filename):
    """Securely serve PDF resumes for the logged-in user."""
    if 'username' not in session:
        return "Unauthorized", 401
    
    # Path traversal protection: resolve and secure path
    safe_filename = secure_filename(filename)
    user_upload_dir = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], session['username']))
    file_path = os.path.abspath(os.path.join(user_upload_dir, safe_filename))
    
    # Verify the file is actually inside the user's directory to prevent traversal attacks
    if not file_path.startswith(user_upload_dir) or not os.path.exists(file_path):
        return "File not found or access denied", 404
        
    from flask import send_from_directory
    return send_from_directory(user_upload_dir, safe_filename)

@app.route('/reset-workspace', methods=['POST'])
def reset_workspace():
    """Wipe all user-uploaded files and clean workspace directory."""
    if 'username' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    # Clear chat session history
    if 'chat_history' in session:
        session.pop('chat_history')
        
    user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    if os.path.exists(user_upload_dir):
        import shutil
        try:
            shutil.rmtree(user_upload_dir)
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to clean workspace directory: {str(e)}"}), 500
            
    return jsonify({"success": True}), 200

@app.route('/chat-resume', methods=['POST'])
def chat_resume():
    """Endpoint for asking a question about a candidate's resume."""
    if 'username' not in session:
        return jsonify({"success": False, "error": "Unauthorized session. Please log in."}), 401
        
    data = request.get_json()
    if not data or 'filename' not in data or 'question' not in data:
        return jsonify({"success": False, "error": "Missing filename or question parameters."}), 400
        
    filename = secure_filename(data['filename'])
    question = data['question'].strip()
    
    if not question:
        return jsonify({"success": False, "error": "Question cannot be empty."}), 400
        
    # Resolve file path securely
    user_upload_dir = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], session['username']))
    file_path = os.path.abspath(os.path.join(user_upload_dir, filename))
    
    # Verify file ownership and existence
    if not file_path.startswith(user_upload_dir) or not os.path.exists(file_path):
        return jsonify({"success": False, "error": "Resume file not found or access denied."}), 404
        
    try:
        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)
        
        # Retrieve history for this candidate
        chat_history = session.get('chat_history', {}).get(filename, [])
        
        app.logger.info(f"[CHAT-INPUT] Filename: {filename}, Question: {question}")
        
        # Get AI response answer
        answer = answer_resume_question(resume_text, question, chat_history)
        
        app.logger.info(f"[CHAT-OUTPUT] Answer: {answer}")
        
        # Update and save history in session
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "model", "content": answer})
        
        if 'chat_history' not in session:
            session['chat_history'] = {}
        session['chat_history'][filename] = chat_history
        session.modified = True
        
        return jsonify({
            "success": True,
            "answer": answer
        }), 200
        
    except Exception as e:
        app.logger.error(f"[ERROR] Exception during chat request: {e}")
        return jsonify({
            "success": False,
            "error": f"An error occurred while scanning the resume: {str(e)}"
        }), 500

# --- JSON API Error Handlers ---

@app.errorhandler(404)
def resource_not_found(e):
    """Handle 404 errors with JSON formatting."""
    return jsonify({
        "success": False,
        "error": "The requested API endpoint was not found."
    }), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors with JSON formatting."""
    return jsonify({
        "success": False,
        "error": "An unexpected internal server error occurred."
    }), 500

if __name__ == '__main__':
    # Run server in debug mode
    app.run(debug=True)
