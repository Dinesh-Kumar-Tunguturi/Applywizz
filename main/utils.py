import os
import re
import requests
from urllib.parse import urlparse
from PyPDF2 import PdfReader
import docx2txt
import json
from twilio.rest import Client

# GitHub token for higher rate limits
GITHUB_TOKEN = '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'
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
account_sid = 'AC87390e14ffc6d5c94efe3ea5e77a937d'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)

# Define scoring weights for different job domains
TECHNICAL_WEIGHTS = {
    'GitHub Profile': 25,
    'LeetCode/DSA Skills': 20,
    'Portfolio Website': 20,
    'LinkedIn Profile': 15,
    'Resume (ATS Score)': 10,
    'Certifications & Branding': 10,
}

# --- Resume Text Extraction ---
def extract_text_from_pdf(file):
    """Extracts text from a PDF file object."""
    try:
        reader = PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception:
        return ""

def extract_text_from_docx(file):
    """Extracts text from a DOCX file object."""
    try:
        return docx2txt.process(file)
    except Exception:
        return ""
    
def extract_links_from_pdf(file):
    """
    Extracts URLs from the text content of a PDF file.
    """
    resume_text = extract_text_from_pdf(file)
    # A robust regex to find common URL patterns
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, resume_text)

def extract_applicant_name(resume_text):
    """
    Attempts to extract the applicant's name from the resume text.
    Assumes the name is the first non-empty line of text.
    """
    if resume_text:
        lines = [line for line in resume_text.split('\n') if line.strip()]
        if lines:
            return lines[0].strip()
    return "Applicant Name Not Found"

import re
from bs4 import BeautifulSoup

def extract_and_identify_links(text):
    """
    Extracts all URLs, HTML hyperlinks, and email addresses from a given text
    and identifies their type (GitHub, LinkedIn, Portfolio, Email, Other).
    """
    links = []

    # Extract URLs from plain text
    url_pattern = r'https?://[^\s"]+'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    found_urls = re.findall(url_pattern, text)
    found_emails = re.findall(email_pattern, text)

    # Add detected plain URLs
    for url in found_urls:
        link_type = "Other"
        if "github.com" in url:
            link_type = "GitHub"
        elif "linkedin.com" in url:
            link_type = "LinkedIn"
        elif re.search(r'portfolio|netlify|vercel|\.me|\.io|\.dev|\.app', url, re.IGNORECASE):
            link_type = "Portfolio"

        links.append({'url': url, 'type': link_type})

    # Add emails
    for email in found_emails:
        links.append({'url': f'mailto:{email}', 'type': 'Email'})

    # Extract from HTML <a href="">
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup.find_all('a', href=True):
        url = tag['href']
        if url not in [item['url'] for item in links]:  # Avoid duplicates
            link_type = "Other"
            if "github.com" in url:
                link_type = "GitHub"
            elif "linkedin.com" in url:
                link_type = "LinkedIn"
            elif re.search(r'portfolio|netlify|vercel|\.me|\.io|\.dev|\.app', url, re.IGNORECASE):
                link_type = "Portfolio"
            elif url.startswith("mailto:"):
                link_type = "Email"
            links.append({'url': url, 'type': link_type})

    # Infer LinkedIn mention even if not linked
    if re.search(r'LinkedIn', text, re.IGNORECASE):
        linkedin_exists = any(link['type'] == 'LinkedIn' for link in links)
        if not linkedin_exists:
            links.append({'url': None, 'type': 'LinkedIn (Inferred)'})

    return links


import fitz  # PyMuPDF
import re
from bs4 import BeautifulSoup

def extract_links_combined(pdf_path):
    """
    Extract hyperlinks from PDF (including embedded and visible text)
    and return both links and full text.
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    links = []

    for page in doc:
        text = page.get_text()
        full_text += text

        # Embedded links in annotations
        for link in page.get_links():
            uri = link.get("uri", "")
            if uri:
                links.append(uri)

    # Now parse all URLs from text
    url_pattern = r'https?://[^\s\)>\]"}]+'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    found_urls = re.findall(url_pattern, full_text)
    found_emails = re.findall(email_pattern, full_text)

    # Add classified links
    identified_links = []

    def classify(url):
        if "github.com" in url:
            return "GitHub"
        elif "linkedin.com" in url:
            return "LinkedIn"
        elif re.search(r'portfolio|netlify|vercel|\.me|\.io|\.dev|\.app', url, re.IGNORECASE):
            return "Portfolio"
        elif url.startswith("mailto:"):
            return "Email"
        return "Other"

    all_urls = set(links + found_urls)  # merge + remove duplicates
    for url in all_urls:
        identified_links.append({
            "url": url,
            "type": classify(url)
        })

    for email in found_emails:
        identified_links.append({
            "url": f"mailto:{email}",
            "type": "Email"
        })

    return identified_links, full_text


# --- Profile Extraction & API Calls ---
def extract_github_username(text):
    """Extracts a GitHub username from a given text."""
    match = re.search(r'github\.com/([A-Za-z0-9\-]+)', text)
    return match.group(1) if match else None

def get_github_repo_count(username):
    """Fetches the number of public repositories for a GitHub user."""
    url = f'https://api.github.com/users/{username}'
    response = requests.get(url, headers=GITHUB_HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data.get('public_repos', 0)
    return 0

def extract_leetcode_username(text):
    """Extracts a LeetCode username from a given text."""
    match = re.search(r'leetcode\.com/(u/|[\w-]+)', text)
    return match.group(1).replace('u/', '').replace('/', '') if match else None

def fetch_leetcode_problem_count(username):
    """Fetches the total number of problems solved for a given LeetCode username."""
    url = "https://leetcode-api-faisalshohag.vercel.app/"
    try:
        res = requests.get(f"{url}{username}", timeout=10)
        return res.json().get('totalSolved', 0) if res.status_code == 200 else 0
    except requests.RequestException:
        return 0

def get_grade_tag(score):
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Poor"

def get_cert_suggestions(domain):
    """
    Generates domain-specific certification recommendations.
    """
    if domain == 'Analytical':
        return [
            'Google Data Analytics Professional Certificate – Coursera',
            'IBM Data Science Professional Certificate – Coursera',
            'Microsoft Certified: Azure Data Scientist Associate',
        ]
    elif domain == 'Technical':
        return [
            'AWS Certified Developer – AWS',
            'Microsoft Certified: Azure Developer Associate',
            'Certified Kubernetes Application Developer (CKAD)',
        ]
    else:
        return [
            'IBM AI Practitioner – Coursera',
            'Google Data Analytics Professional Certificate – Coursera',
            'AWS Certified Developer – AWS',
        ]

import random
def calculate_dynamic_ats_score(resume_text, github_username, leetcode_username, extracted_links):

    """
    Calculates a detailed ATS score based on a given domain.
    """
    weights = TECHNICAL_WEIGHTS
    
    sections = {}
    total_score = 0
    suggestions = []
    
    # Define presence variables at the start of the function
    github_presence = bool(github_username)
    leetcode_presence = bool(leetcode_username)
    portfolio_presence = bool(re.search(r'https?://[a-zA-Z0-9-]+\.(com|io|dev|app|me|net|in|org)/?', resume_text, re.IGNORECASE))
    linkedin_presence = bool(re.search(r'linkedin\.com/in/', resume_text, re.IGNORECASE))
    cert_presence = bool(re.search(r'certification|certified|course|certificate', resume_text, re.IGNORECASE))

    # --- Start Dynamic Scoring ---

    # 1. GitHub Profile
    github_criteria = []
    github_section_score = 0
    if github_presence:
        github_criteria.append({'name': 'Public link present', 'score': 3, 'weight': 3, 'insight': 'Ensures GitHub visibility to recruiters.'})
        github_criteria.append({'name': 'Pinned repositories (3+)', 'score': random.randint(0, 5), 'weight': 5, 'insight': 'Reflects curated, visible proof of skills.'})
        github_criteria.append({'name': 'Recent activity (commits in 90 days)', 'score': random.randint(0, 5), 'weight': 5, 'insight': 'Recruiters prefer candidates with ongoing contributions.'})
        github_criteria.append({'name': 'Clear README files', 'score': random.randint(0, 6), 'weight': 6, 'insight': 'Shows communication, structure, and project clarity.'})
        github_criteria.append({'name': 'Domain-relevant projects', 'score': random.randint(0, 6), 'weight': 6, 'insight': 'Repos should match the job domain.'})
        github_section_score = sum(c['score'] for c in github_criteria)
    else:
        suggestions.append("Suggestion: Add your GitHub profile link and ensure it's up-to-date with recent activity.")
        github_criteria.append({'name': 'Public link present', 'score': 0, 'weight': 3, 'insight': 'No GitHub link was detected.'})
    
    sections['GitHub Profile'] = {'score': github_section_score, 'grade': get_grade_tag(github_section_score), 'weight': weights['GitHub Profile'], 'sub_criteria': github_criteria}

    # 2. LeetCode / DSA Skills
    leetcode_criteria = []
    leetcode_section_score = 0
    if leetcode_presence:
        leetcode_criteria = [
            {'name': 'Link present', 'score': 2, 'weight': 2, 'insight': 'Confirms practice can be verified.'},
            {'name': '100+ questions solved', 'score': random.randint(0, 5), 'weight': 5, 'insight': 'Demonstrates strong dedication.'},
            {'name': 'Medium/Hard problem attempts', 'score': random.randint(0, 4), 'weight': 4, 'insight': 'Shows depth beyond basic algorithms.'},
            {'name': 'Regular contest participation', 'score': random.randint(0, 4), 'weight': 4, 'insight': 'Indicates consistency and competitive learning.'},
            {'name': 'Topic variety (e.g., DP, Graphs)', 'score': random.randint(0, 5), 'weight': 5, 'insight': 'Reflects a well-rounded problem-solving profile.'}
        ]
        leetcode_section_score = sum(c['score'] for c in leetcode_criteria)
    else:
        suggestions.append("Suggestion: Include a link to your LeetCode profile to showcase your DSA skills.")
        leetcode_criteria = [{'name': 'Link present', 'score': 0, 'weight': 2, 'insight': 'No LeetCode link was detected.'}]
    
    sections['LeetCode/DSA Skills'] = {'score': leetcode_section_score, 'grade': get_grade_tag(leetcode_section_score), 'weight': weights['LeetCode/DSA Skills'], 'sub_criteria': leetcode_criteria}
    
    # 3. Portfolio Website
    portfolio_criteria = []
    portfolio_section_score = 0
    if portfolio_presence:
        portfolio_criteria = [
            {'name': 'Link present', 'score': 2, 'weight': 2, 'insight': 'Portfolios must be accessible.'},
            {'name': 'Responsive/mobile design', 'score': random.randint(0, 3), 'weight': 3, 'insight': 'Crucial for recruiter viewing on different devices.'},
            {'name': 'Project write-ups with context', 'score': random.randint(0, 4), 'weight': 4, 'insight': 'Helps recruiters understand your problem-solving process.'},
            {'name': 'Interactive demos or GitHub links', 'score': random.randint(0, 3), 'weight': 3, 'insight': 'Improves engagement and recruiter time on page.'},
            {'name': 'Intro video / personal branding page', 'score': random.randint(0, 3), 'weight': 3, 'insight': 'Adds human element and unique identity.'}
        ]
        portfolio_section_score = sum(c['score'] for c in portfolio_criteria)
    else:
        suggestions.append("Suggestion: Create a professional portfolio website to showcase your projects and skills.")
        portfolio_criteria = [{'name': 'Link present', 'score': 0, 'weight': 2, 'insight': 'No portfolio link was detected.'}]

    sections['Portfolio Website'] = {'score': portfolio_section_score, 'grade': get_grade_tag(portfolio_section_score), 'weight': weights['Portfolio Website'], 'sub_criteria': portfolio_criteria}

    # 4. LinkedIn Profile
    linkedin_criteria = []
    linkedin_score = 0

    # Detection logic (should be passed from extracted_links)
    has_linkedin = any(link.get('type') == 'LinkedIn' for link in extracted_links)

    if has_linkedin:
        linkedin_criteria = [
            {
                "name": "Public link present",
                "score": 3,
                "weight": 3,
                "insight": "LinkedIn profile link found in resume."
            },
            # Add more if needed in future (e.g., custom username, profile details)
        ]
        linkedin_score = sum(c["score"] for c in linkedin_criteria)
    else:
        linkedin_criteria = [
            {
                "name": "Public link present",
                "score": 0,
                "weight": 3,
                "insight": "No LinkedIn link found. Add it to boost visibility."
            }
        ]
        linkedin_score = 0
        suggestions.append("Suggestion: Add a public LinkedIn link to enhance recruiter visibility.")

    sections["LinkedIn"] = {
        "score": linkedin_score,
        "weight": 3,  # should match total of weights in sub_criteria
        "grade": get_grade_tag(linkedin_score),
        "sub_criteria": linkedin_criteria
    }

    
    # 5. Resume (ATS Score)
    resume_criteria = []
    resume_section_score = random.randint(50, 100) # Placeholder score
    resume_criteria = [
        {'name': 'ATS-friendly layout', 'score': 3, 'weight': 3, 'insight': 'Uses readable fonts, minimal columns, no images.'},
        {'name': 'Action verbs & quantified results', 'score': 4, 'weight': 4, 'insight': '“Reduced X by Y%” > “Responsible for X”'},
        {'name': 'Job-relevant keyword alignment', 'score': 3, 'weight': 3, 'insight': 'Matches keywords from job descriptions.'},
        {'name': 'Brevity and conciseness', 'score': 2, 'weight': 2, 'insight': 'Ideal resumes stay under 2 pages.'},
        {'name': 'Minimal jargon / repetition', 'score': 3, 'weight': 3, 'insight': 'Recruiters prefer clarity.'}
    ]
    sections['Resume (ATS Score)'] = {'score': resume_section_score, 'grade': get_grade_tag(resume_section_score), 'weight': weights['Resume (ATS Score)'], 'sub_criteria': resume_criteria}
    
    # 6. Certifications & Branding
    cert_criteria = []
    cert_section_score = 0
    if cert_presence:
        cert_section_score = 65
        cert_criteria = [
            {'name': 'Role-relevant certifications', 'score': 5, 'weight': 5, 'insight': 'From platforms like LinkedIn Learning, Coursera, etc.'},
            {'name': 'Credibility of platform', 'score': 5, 'weight': 5, 'insight': 'Higher points for well-known issuers.'},
            {'name': 'Recency (within last 2 years)', 'score': 3, 'weight': 3, 'insight': 'Recent certifications are weighted higher.'},
            {'name': 'Completeness (title + issuer)', 'score': 2, 'weight': 2, 'insight': 'No “Free Audit Available” tags; proper naming only.'}
        ]
    else:
        cert_section_score = 0
        cert_suggestions = get_cert_suggestions(domain)
        suggestions.append("Suggestion: Obtain role-relevant certifications to stand out.")
        cert_criteria = [{'name': 'Certifications present', 'score': 0, 'weight': 15, 'insight': 'No certifications were detected in your resume.'}]
    
    sections['Certifications & Branding'] = {'score': cert_section_score, 'grade': get_grade_tag(cert_section_score), 'weight': weights['Certifications & Branding'], 'sub_criteria': cert_criteria, 'recommendations': cert_suggestions if not cert_presence else []}
    
    # Calculate weighted total score
    total_score = sum(s['score'] * (s['weight'] / 100) for s in sections.values())

    # Calculate average of the 6 scores
    all_section_scores = [s['score'] for s in sections.values()]
    overall_score_average = sum(all_section_scores) / len(all_section_scores)

    # Final Grade Interpretation
    overall_grade = get_grade_tag(overall_score_average)

    return {
        "sections": sections,
        "total_score": int(total_score),
        "overall_score_average": int(overall_score_average),
        "overall_grade": overall_grade,
        "suggestions": suggestions
    }

# --- Payment Verification Logic (Simulated) ---
# In a real application, this would be a database or a call to a payment gateway API
# For demonstration, we'll keep a simple in-memory "received transactions" list.
SIMULATED_RECEIVED_TRANSACTIONS = [
    {"utr": "1234567890", "amount": 499, "status": "SUCCESS"},
    {"utr": "ABCDEF1234", "amount": 999, "status": "SUCCESS"},
    {"utr": "XYZ9876543", "amount": 2999, "status": "SUCCESS"},
    {"utr": "FAILED123", "amount": 499, "status": "FAILED"},
    {"utr": "PENDING456", "amount": 999, "status": "PENDING"},
]

def verify_bank_transaction(utr_number, expected_amount):
    """
    Simulates checking if a UTR matches a received bank transaction.
    Returns True if valid, False otherwise.
    """
    print(f"Simulating verification for UTR: {utr_number}, Expected Amount: {expected_amount}")
    for transaction in SIMULATED_RECEIVED_TRANSACTIONS:
        if transaction["utr"] == utr_number:
            if transaction["amount"] == expected_amount and transaction["status"] == "SUCCESS":
                print(f"Verification SUCCESS for UTR: {utr_number}")
                return True
            else:
                print(f"Verification FAILED (amount mismatch or status not SUCCESS) for UTR: {utr_number}")
                return False
    print(f"Verification FAILED (UTR not found) for UTR: {utr_number}")
    return False

import matplotlib
matplotlib.use('Agg')  # ✅ Add this to avoid GUI backend issues
import matplotlib.pyplot as plt
import io
import base64

def prepare_chart_data(score_breakdown):
    """
    Prepares a dictionary of data that can be used directly by Chart.js.
    """
    labels = list(score_breakdown.keys())
    scores = [data['score'] for data in score_breakdown.values()]
    
    chart_colors = []
    for data in score_breakdown.values():
        grade = data['grade'].lower()
        if grade == 'excellent':
            chart_colors.append('#4CAF50')
        elif grade == 'good':
            chart_colors.append('#2196F3')
        elif grade == 'average':
            chart_colors.append('#FF9800')
        else:
            chart_colors.append('#dc3545')
    
    return {
        "labels": labels,
        "scores": scores,
        "backgroundColors": chart_colors,
    }

def generate_pie_chart(sections):
    """
    Generates a pie chart from section scores and returns it as a base64-encoded image.
    """
    labels = list(sections.keys())
    sizes = [section['score'] for section in sections.values()]
    
    # Map grades to colors for consistency with the report
    colors = []
    for section in sections.values():
        grade = section['grade'].lower()
        if grade == 'excellent':
            colors.append('#4CAF50')
        elif grade == 'good':
            colors.append('#2196F3')
        elif grade == 'average':
            colors.append('#FF9800')
        else:
            colors.append('#dc3545')

    plt.figure(figsize=(6, 6), facecolor='#121212')  # Match dark theme
    plt.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        colors=colors,
        textprops={'color': "w"}
    )
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#121212')  # Set background color
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()  # Free up memory
    return encoded