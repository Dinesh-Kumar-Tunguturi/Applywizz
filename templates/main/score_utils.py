import os
import re
import requests
from PyPDF2 import PdfReader
import docx2txt

# GitHub token for higher rate limits
GITHUB_TOKEN = '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'
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

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

def calculate_dynamic_ats_score(resume_text, github_username, leetcode_username, domain='Technical'):
    """
    Calculates a detailed ATS score based on a given domain.
    """
    weights = TECHNICAL_WEIGHTS
    
    sections = {}
    total_score = 0
    suggestions = []
    
    # Placeholder scores for a dynamic feel
    github_score = 85 if bool(github_username) else 0
    leetcode_score = 72 if bool(leetcode_username) else 0
    portfolio_score = 68 if re.search(r'portfolio\.com|netlify\.app|vercel\.app', resume_text, re.IGNORECASE) else 0
    linkedin_score = 75 if re.search(r'linkedin\.com/in/', resume_text, re.IGNORECASE) else 0
    resume_score = 82 if re.search(r'\d+[%$]|increase|decrease|ats-friendly', resume_text, re.IGNORECASE) else 0
    cert_score = 65 if re.search(r'certification|certified|course|certificate', resume_text, re.IGNORECASE) else 0

    # 1. GitHub Profile
    github_criteria = []
    github_presence = bool(github_username)
    if github_presence:
        github_criteria = [
            {'name': 'Public link present', 'score': 3, 'weight': 3, 'insight': 'Ensures GitHub visibility to recruiters.'},
            {'name': 'Pinned repositories (3+)', 'score': 5, 'weight': 5, 'insight': 'Reflects curated, visible proof of skills.'},
            {'name': 'Recent activity (commits in 90 days)', 'score': 5, 'weight': 5, 'insight': 'Recruiters prefer candidates with ongoing contributions.'},
            {'name': 'Clear README files', 'score': 6, 'weight': 6, 'insight': 'Shows communication, structure, and project clarity.'},
            {'name': 'Domain-relevant projects', 'score': 6, 'weight': 6, 'insight': 'Repos should match the job domain.'}
        ]
    else:
        suggestions.append("Suggestion: Add your GitHub profile link and ensure it's up-to-date with recent activity.")
        github_criteria = [{'name': 'Public link present', 'score': 0, 'weight': 3, 'insight': 'No GitHub link was detected.'}]
    
    sections['GitHub Profile'] = {'score': github_score, 'grade': get_grade_tag(github_score), 'weight': weights['GitHub Profile'], 'sub_criteria': github_criteria}
    total_score += github_score * (weights['GitHub Profile'] / 100)

    # 2. LeetCode / DSA Skills
    leetcode_criteria = []
    leetcode_presence = bool(leetcode_username)
    if leetcode_presence:
        leetcode_criteria = [
            {'name': 'Link present', 'score': 2, 'weight': 2, 'insight': 'Confirms practice can be verified.'},
            {'name': '100+ questions solved', 'score': 5, 'weight': 5, 'insight': 'Demonstrates strong dedication.'},
            {'name': 'Medium/Hard problem attempts', 'score': 4, 'weight': 4, 'insight': 'Shows depth beyond basic algorithms.'},
            {'name': 'Regular contest participation', 'score': 4, 'weight': 4, 'insight': 'Indicates consistency and competitive learning.'},
            {'name': 'Topic variety (e.g., DP, Graphs)', 'score': 5, 'weight': 5, 'insight': 'Reflects a well-rounded problem-solving profile.'}
        ]
    else:
        leetcode_score = 0
        suggestions.append("Suggestion: Include a link to your LeetCode profile to showcase your DSA skills.")
        leetcode_criteria = [{'name': 'Link present', 'score': 0, 'weight': 2, 'insight': 'No LeetCode link was detected.'}]
    
    sections['LeetCode/DSA Skills'] = {'score': leetcode_score, 'grade': get_grade_tag(leetcode_score), 'weight': weights['LeetCode/DSA Skills'], 'sub_criteria': leetcode_criteria}
    total_score += leetcode_score * (weights['LeetCode/DSA Skills'] / 100)

    # 3. Portfolio Website
    portfolio_criteria = []
    portfolio_presence = bool(re.search(r'portfolio\.com|netlify\.app|vercel\.app', resume_text, re.IGNORECASE))
    if portfolio_presence:
        portfolio_criteria = [
            {'name': 'Link present', 'score': 2, 'weight': 2, 'insight': 'Portfolios must be accessible.'},
            {'name': 'Responsive/mobile design', 'score': 3, 'weight': 3, 'insight': 'Crucial for recruiter viewing on different devices.'},
            {'name': 'Project write-ups with context', 'score': 4, 'weight': 4, 'insight': 'Helps recruiters understand your problem-solving process.'},
            {'name': 'Interactive demos or GitHub links', 'score': 3, 'weight': 3, 'insight': 'Improves engagement and recruiter time on page.'},
            {'name': 'Intro video / personal branding page', 'score': 3, 'weight': 3, 'insight': 'Adds human element and unique identity.'}
        ]
    else:
        portfolio_score = 0
        suggestions.append("Suggestion: Create a professional portfolio website to showcase your projects and skills.")
        portfolio_criteria = [{'name': 'Link present', 'score': 0, 'weight': 2, 'insight': 'No portfolio link was detected.'}]

    sections['Portfolio Website'] = {'score': portfolio_score, 'grade': get_grade_tag(portfolio_score), 'weight': weights['Portfolio Website'], 'sub_criteria': portfolio_criteria}
    total_score += portfolio_score * (weights['Portfolio Website'] / 100)

    # 4. LinkedIn Profile
    linkedin_criteria = []
    linkedin_presence = bool(re.search(r'linkedin\.com/in/', resume_text, re.IGNORECASE))
    if linkedin_presence:
        linkedin_criteria = [
            {'name': 'Link present', 'score': 1, 'weight': 1, 'insight': 'Minimum presence requirement.'},
            {'name': 'Headline & Summary filled', 'score': 2, 'weight': 2, 'insight': 'Should be sharp, relevant, and domain-focused.'},
            {'name': 'Skills & Endorsements', 'score': 2, 'weight': 2, 'insight': 'Reinforces resume claims.'},
            {'name': 'GitHub/Portfolio linked', 'score': 2, 'weight': 2, 'insight': 'Ensures the recruiter can deep-dive instantly.'},
            {'name': 'Recent posts or activity', 'score': 3, 'weight': 3, 'insight': 'Recruiters prefer active, engaged candidates.'}
        ]
    else:
        linkedin_score = 0
        suggestions.append("Suggestion: Add a link to your LinkedIn profile to expand your professional network.")
        linkedin_criteria = [{'name': 'Link present', 'score': 0, 'weight': 1, 'insight': 'No LinkedIn link was detected.'}]
    
    sections['LinkedIn Profile'] = {'score': linkedin_score, 'grade': get_grade_tag(linkedin_score), 'weight': weights['LinkedIn Profile'], 'sub_criteria': linkedin_criteria}
    total_score += linkedin_score * (weights['LinkedIn Profile'] / 100)
    
    # 5. Resume (ATS Score)
    resume_criteria = []
    if re.search(r'\d+[%$]|increase|decrease|ats-friendly', resume_text, re.IGNORECASE):
        resume_score = 82
    else:
        resume_score = 0
    
    resume_criteria = [
        {'name': 'ATS-friendly layout', 'score': 3, 'weight': 3, 'insight': 'Uses readable fonts, minimal columns, no images.'},
        {'name': 'Action verbs & quantified results', 'score': 4, 'weight': 4, 'insight': '“Reduced X by Y%” > “Responsible for X”'},
        {'name': 'Job-relevant keyword alignment', 'score': 3, 'weight': 3, 'insight': 'Matches keywords from job descriptions.'},
        {'name': 'Brevity and conciseness', 'score': 2, 'weight': 2, 'insight': 'Ideal resumes stay under 2 pages.'},
        {'name': 'Minimal jargon / repetition', 'score': 3, 'weight': 3, 'insight': 'Recruiters prefer clarity.'}
    ]
    
    sections['Resume (ATS Score)'] = {'score': resume_score, 'grade': get_grade_tag(resume_score), 'weight': weights['Resume (ATS Score)'], 'sub_criteria': resume_criteria}
    total_score += resume_score * (weights['Resume (ATS Score)'] / 100)
    
    # 6. Certifications & Branding
    cert_criteria = []
    cert_presence = bool(re.search(r'certification|certified|course|certificate', resume_text, re.IGNORECASE))
    if cert_presence:
        cert_score = 65
        cert_criteria = [
            {'name': 'Role-relevant certifications', 'score': 5, 'weight': 5, 'insight': 'From platforms like LinkedIn Learning, Coursera, etc.'},
            {'name': 'Credibility of platform', 'score': 5, 'weight': 5, 'insight': 'Higher points for well-known issuers.'},
            {'name': 'Recency (within last 2 years)', 'score': 3, 'weight': 3, 'insight': 'Recent certifications are weighted higher.'},
            {'name': 'Completeness (title + issuer)', 'score': 2, 'weight': 2, 'insight': 'No “Free Audit Available” tags; proper naming only.'}
        ]
    else:
        cert_score = 0
        cert_suggestions = get_cert_suggestions(domain)
        suggestions.append("Suggestion: Obtain role-relevant certifications to stand out.")
        cert_criteria = [{'name': 'Certifications present', 'score': 0, 'weight': 15, 'insight': 'No certifications were detected in your resume.'}]
    
    sections['Certifications & Branding'] = {'score': cert_score, 'grade': get_grade_tag(cert_score), 'weight': weights['Certifications & Branding'], 'sub_criteria': cert_criteria, 'recommendations': cert_suggestions if not cert_presence else []}
    total_score += cert_score * (weights['Certifications & Branding'] / 100)

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
# This list would be populated by actual payment gateway webhooks in production.
SIMULATED_RECEIVED_TRANSACTIONS = [
    {"utr": "1234567890", "amount": 499, "status": "SUCCESS"},
    {"utr": "ABCDEF1234", "amount": 999, "status": "SUCCESS"},
    {"utr": "XYZ9876543", "amount": 2999, "status": "SUCCESS"},
    # Add more simulated transactions for testing different scenarios
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