import PyPDF2
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import nltk

# Download the required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab') # This is the missing resource mentioned in the error

# --- 1. PDF Text Extraction Function ---
def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from a PDF file.
    """
    full_text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
    return full_text

# --- 2. Preprocessing Function ---
def preprocess_text(text):
    """
    Cleans and tokenizes text for NLP analysis.
    """
    if not text:
        return ""
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text, re.I|re.A)
    # Tokenize and convert to lowercase
    tokens = word_tokenize(text.lower())
    # Remove stopwords and lemmatize
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return " ".join(filtered_tokens)

# --- 3. ATS Score Calculation Function ---
def calculate_ats_score(resume_text, job_description_text):
    """
    Calculates the ATS score using TF-IDF and Cosine Similarity.
    """
    preprocessed_resume = preprocess_text(resume_text)
    preprocessed_jd = preprocess_text(job_description_text)
    
    if not preprocessed_resume or not preprocessed_jd:
        return 0.0

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([preprocessed_resume, preprocessed_jd])
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    score = round(cosine_sim[0][0] * 100, 2)
    
    return score

# --- 4. Main Script ---
if __name__ == "__main__":
    
    # 📌 The line below is where you specify the path to your PDF resume file.
    # Replace "resume.pdf" with the actual path.
    resume_pdf_path = "Dinesh_resume...pdf" 
    
    job_description = """
    We are seeking a Software Engineer with a strong background in Python and Java. The ideal candidate will have 
    experience with cloud technologies such as Docker and Kubernetes. A solid understanding of Machine Learning 
    and Natural Language Processing (NLP) techniques is highly desirable.
    """
    
    resume_text = extract_text_from_pdf(resume_pdf_path)
    
    if resume_text:
        ats_score = calculate_ats_score(resume_text, job_description)
        print(f"The ATS score for the resume is: {ats_score}%")
    else:
        print("Failed to extract text from the PDF. Please check the file path and format.")