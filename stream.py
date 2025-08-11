import streamlit as st
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import io

def extract_text_from_pdf(file_stream):
    """
    Extracts all text from an uploaded PDF file stream.
    """
    full_text = ""
    try:
        reader = PyPDF2.PdfReader(file_stream)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None
    return full_text

def preprocess_text(text):
    """
    Cleans text for NLP analysis by removing special characters and standardizing.
    """
    if not text:
        return ""
    text = re.sub(r'[^a-zA-Z\s]', '', text, re.I | re.A)
    return text.lower()

def calculate_ats_score(resume_text, job_description_text):
    """
    Calculates the ATS score using TF-IDF vectorization and cosine similarity.
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

# --- Streamlit UI ---
st.title("📄 ATS Resume Matcher")
st.markdown("Upload your resume and a job description to get a compatibility score.")

uploaded_file = st.file_uploader("Choose your resume (PDF only)", type=["pdf"])
job_description = st.text_area("Paste the job description here", height=200)


if st.button("Calculate ATS Score"):
    if uploaded_file is not None and job_description:
        if uploaded_file.name.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(io.BytesIO(uploaded_file.read()))

            if resume_text:
                ats_score = calculate_ats_score(resume_text, job_description)
                st.success(f"**The ATS compatibility score is: {ats_score}%**")
            else:
                st.error("Failed to extract text from the PDF. Please try a different file.")
        else:
            st.error("Please upload a valid PDF file.")
    else:
        st.warning("Please upload a resume and paste a job description to calculate the score.")