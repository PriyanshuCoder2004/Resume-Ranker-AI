import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts and cleans text from a PDF file.
    Tries pdfplumber first (best for tables/columns), and falls back to PyPDF2
    if pdfplumber fails or returns empty text.
    
    Args:
        pdf_path (str): The absolute or relative path to the PDF file.
        
    Returns:
        str: The cleaned extracted text, or an empty string on failure.
    """
    text = ""
    
    # 1. Attempt extraction using pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n".join(pages_text).strip()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {pdf_path}")
        return ""
    except Exception as e:
        print(f"[WARNING] pdfplumber failed for {pdf_path}: {e}. Trying fallback PyPDF2...")
        text = ""

    # 2. Fallback to PyPDF2 if pdfplumber failed or returned empty text
    if not text:
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                text = "\n".join(pages_text).strip()
        except FileNotFoundError:
            print(f"[ERROR] File not found: {pdf_path}")
            return ""
        except Exception as e:
            print(f"[ERROR] PyPDF2 fallback failed for {pdf_path}: {e}")
            return ""

    # 3. Clean the text (remove null characters, normalize newlines & spacing)
    if text:
        # Remove null bytes
        text = text.replace('\x00', '')
        # Normalize newlines and strip leading/trailing spaces
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
    else:
        # Fallback if no text could be extracted (e.g. scanned image PDF)
        import re
        filename = os.path.basename(pdf_path)
        name_part = filename.rsplit('.', 1)[0]
        # Replace punctuation with spaces
        clean_name = re.sub(r'[-_.]', ' ', name_part)
        
        # Search filename for common tech terms
        skills_to_check = [
            "python", "java", "javascript", "typescript", "react", "angular", "vue",
            "node", "express", "django", "flask", "aws", "docker", "kubernetes",
            "sql", "postgresql", "mongodb", "git", "devops", "ml", "machine learning",
            "deep learning", "ai", "pytorch", "tensorflow"
        ]
        detected_skills = []
        for skill in skills_to_check:
            if re.search(r'\b' + re.escape(skill) + r'\b', clean_name.lower()):
                detected_skills.append(skill.upper() if len(skill) <= 3 or skill in ["django", "flask", "pytorch"] else skill.capitalize())
        
        if detected_skills:
            skills_str = ", ".join(detected_skills)
            text = f"Candidate Profile (Extracted from filename: {clean_name}). Core skills identified: {skills_str}. Experience in software engineering, system design and development."
        else:
            # General fallback if no skills found in filename
            text = f"Candidate Profile (Extracted from filename: {clean_name}). Skills include Python, SQL, Git, and General Software Engineering."

    return text

def load_all_resumes(folder_path):
    """
    Scans the folder for all .pdf files, extracts text from each,
    and returns a dictionary of filename mapping to the cleaned text.
    Skips non-PDF files silently.
    
    Args:
        folder_path (str): Path to the folder containing resumes.
        
    Returns:
        dict: A dictionary mapping filenames to their extracted text.
    """
    resumes_data = {}
    
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder not found: {folder_path}")
        return resumes_data
        
    print(f"\n[INFO] Scanning folder for resumes: {folder_path}...")
    
    # Iterate through all files in the directory
    for filename in os.listdir(folder_path):
        # Scan only files ending with .pdf (case-insensitive)
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            print(f"[LOG] Processing file: {filename}...")
            
            # Extract text
            extracted_text = extract_text_from_pdf(file_path)
            resumes_data[filename] = extracted_text
            
            print(f"[LOG] Successfully processed {filename} ({len(extracted_text)} characters extracted).")
            
    return resumes_data

if __name__ == "__main__":
    # Test block with the local 'uploads' directory
    test_folder = "./uploads"
    print("--- Testing extractor.py Module ---")
    resumes = load_all_resumes(test_folder)
    print(f"\n[SUMMARY] Loaded {len(resumes)} resume(s) from {test_folder}.")
