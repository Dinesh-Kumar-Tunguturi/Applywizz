import os
import random
import re
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.conf import settings
from twilio.rest import Client
from .utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_applicant_name,
    extract_github_username,
    extract_leetcode_username,
    calculate_dynamic_ats_score,
    verify_bank_transaction
)
from .forms import PaymentDetailsForm

# OTP Storage (In-memory, not for production)
otp_storage = {}
signup_otp_storage = {}

# Twilio Credentials (Hardcoded for this example)
from twilio.rest import Client
account_sid = 'AC87390e14ffc6d5c94efe3ea5e77a937d'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)


PLANS = {
    1: {"name": "Applywizz Resume", "price": 499, "description": "Builds a resume with the highest ATS score."},
    2: {"name": "Resume + Profile Portfolio", "price": 999, "description": "Includes Resume building and a professional Portfolio Website."},
    3: {"name": "All-in-One Package", "price": 2999, "description": "Includes Resume, Portfolio, and applying to jobs on your behalf."},
}

# --- Basic Views ---
def landing(request):
    return render(request, "landing.html")

def signin(request):
    return render(request, "signin.html")

def login_view(request):
    return render(request, "login.html")

def signup(request):
    return render(request, "signup.html")

def about_us(request):
    return render(request, "about_us.html")

# --- OTP via Twilio ---
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from twilio.rest import Client

# ✅ Twilio credentials
# account_sid = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
# auth_token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
verify_sid = 'VA93dc536826c0ab37d7894d8b241f09a2'
client = Client(account_sid, auth_token)

@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        mobile = request.POST.get("mobile")
        formatted_number = f"+91{mobile}"
        try:
            client.verify.v2.services(verify_sid).verifications.create(
                to=formatted_number,
                channel='sms'
            )
            return JsonResponse({"status": "success", "message": "OTP sent successfully."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error sending OTP: {str(e)}"})
    return JsonResponse({"status": "error", "message": "Invalid request"})

@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        mobile = request.POST.get("mobile")
        otp = request.POST.get("otp")
        formatted_number = f"+91{mobile}"
        try:
            verification_check = client.verify.v2.services(verify_sid).verification_checks.create(
                to=formatted_number,
                code=otp
            )
            if verification_check.status == "approved":
                return JsonResponse({"status": "success", "redirect_url": "/upload_resume"})
            else:
                return JsonResponse({"status": "error", "message": "Invalid OTP. Try again."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error verifying OTP: {str(e)}"})
    return JsonResponse({"status": "error", "message": "Invalid request"})


# --- OTP via Email ---
def send_signup_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = str(random.randint(1000, 9999))
        signup_otp_storage[email] = otp
        send_mail(
            subject="Your ApplyWizz Signup OTP",
            message=f"Your OTP for ApplyWizz signup is {otp}.",
            from_email="no-reply@applywizz.com",
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({"status": "success", "message": "OTP sent to your email!"})
    return JsonResponse({"status": "error", "message": "Invalid request"})

def verify_signup_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        if signup_otp_storage.get(email) == otp:
            del signup_otp_storage[email]
            return JsonResponse({"status": "success", "redirect_url": "/"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid OTP"})
    return JsonResponse({"status": "error", "message": "Invalid request"})

# --- Main Resume Analyzer Views ---
def upload_resume(request):
    return render(request, 'upload_resume.html')

import matplotlib
matplotlib.use('Agg')  # ✅ Add this to avoid GUI backend issues
import matplotlib.pyplot as plt
import io
import base64

def generate_pie_chart(sections):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import io, base64

    labels = []
    sizes = []
    colors = ['#4CAF50', '#2196F3', '#FF9800', '#dc3545', '#673AB7', '#00BCD4']
    legend_labels = []

    # Filter out NaN, None, or non-numeric scores
    for i, (label, data) in enumerate(sections.items()):
        score = data.get('score', 0)
        if isinstance(score, (int, float)) and not (score is None or score != score):  # NaN check
            labels.append(label)
            sizes.append(score)

    if not sizes or sum(sizes) == 0:
        return None  # Avoid division by zero

    fig, ax = plt.subplots(figsize=(8, 8), facecolor='#121212')
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        colors=colors[:len(labels)],
        textprops={'color': "white", 'fontsize': 14}
    )
    plt.axis('equal')

    # Add legend below the pie chart
    legend_labels = [
        f"{label}: {size:.1f}%" for label, size in zip(labels, sizes)
    ]
    ax.legend(
        wedges,
        legend_labels,
        title="Categories",
        loc='lower center',
        bbox_to_anchor=(0.5, -0.2),
        fontsize=15,
        title_fontsize=14,
        frameon=False,
        labelcolor='white'
    )

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#121212')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return encoded







from .utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_applicant_name,
    extract_github_username,
    extract_leetcode_username,
    calculate_dynamic_ats_score,
    extract_links_from_pdf  # <- Make sure this exists
)
import os
import re


import requests

def fetch_dynamic_certifications(role):
    """
    Fetch recommended certifications dynamically from Coursera.
    You can extend this to LinkedIn Learning, DataCamp, etc.
    """
    query = role.replace(" ", "+")
    url = f"https://api.coursera.org/api/courses.v1?q=search&query={query}&limit=6"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        certs = []
        for item in data.get("elements", []):
            name = item.get("name", "").strip()
            if name:
                certs.append(f"{name} - Coursera")
        return certs[:6]  # Max 6
    except Exception as e:
        print(f"[Error fetching certifications] {e}")
        return []


from main.utils import extract_links_combined 


import os
import re
import tempfile
import requests
from PyPDF2 import PdfReader
from django.shortcuts import render
from .utils import (
    extract_text_from_docx,
    extract_links_combined,
    extract_applicant_name,
    extract_github_username,
    extract_leetcode_username,
    calculate_dynamic_ats_score,
    generate_pie_chart
)

# ---------------- Helper Functions ----------------
def extract_text_from_pdf_resume(file_path):
    """Extract all text from a PDF."""
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_certifications_from_text(resume_text):
    """Extract certifications from resume text."""
    certs_found = []
    for line in resume_text.split("\n"):
        if re.search(r"(certificate|certification|training|course)", line, re.IGNORECASE):
            certs_found.append(line.strip())
    return certs_found


def get_role_based_certifications(role):
    """
    Return up to 6 recommended certifications for the given role.
    This can later be replaced with an API call to Coursera/LinkedIn Learning.
    """
    cert_map = {
        "python developer": [
            "Python for Everybody - Coursera",
            "Google IT Automation with Python - Coursera",
            "Applied Data Science with Python - University of Michigan (Coursera)",
            "Automate the Boring Stuff with Python - Udemy",
            "Data Analysis with Python - freeCodeCamp",
            "Django for Everybody - Coursera"
        ],
        "data analyst": [
            "Google Data Analytics Professional Certificate - Coursera",
            "IBM Data Analyst Professional Certificate - Coursera",
            "Data Analysis with Python - freeCodeCamp",
            "Statistics for Data Science - edX",
            "Excel to MySQL: Analytic Techniques - Coursera",
            "Data Visualization with Tableau - Coursera"
        ],
    }
    return cert_map.get(role.lower(), [])



from django.shortcuts import render, redirect

def analyze_resume(request):
    # Step 1: GET request → show results if they exist
    if request.method == 'GET':
        if 'resume_results' in request.session:
            return render(request, 'resume_result.html', request.session['resume_results'])
        return render(request, 'upload_resume.html')

    # Step 2: POST request → analyze resume, store, and redirect
    if request.method == 'POST' and request.FILES.get('resume'):
        resume_file = request.FILES['resume']
        ext = os.path.splitext(resume_file.name)[1].lower()

        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            for chunk in resume_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        # Extract text and links
        if ext == ".pdf":
            extracted_links, resume_text = extract_links_combined(temp_path)
        elif ext == ".docx":
            resume_text = extract_text_from_docx(resume_file)
            extracted_links = []
        else:
            request.session['resume_results'] = {"error": "Unsupported file format"}
            return redirect('analyze_resume')

        # Name and usernames
        applicant_name = extract_applicant_name(resume_text)
        github_username = extract_github_username(resume_text)
        leetcode_username = extract_leetcode_username(resume_text)

        # Run scoring
        ats_result = calculate_dynamic_ats_score(resume_text, github_username, leetcode_username, extracted_links)
        ats_score = ats_result['sections'].get('Resume (ATS Score)', {}).get('score', 0)
        overall_score_average = ats_result.get('overall_score_average', 0)

        # Detection
        has_github = any("github.com" in link.get("url", "") for link in extracted_links)
        has_linkedin = any("linkedin.com" in link.get("url", "") for link in extracted_links)
        has_email = any(link.get("type") == "Email" for link in extracted_links)

        # Pie chart
        pie_chart_image = generate_pie_chart(ats_result["sections"])

        # Certifications
        existing_certs = [
            line.strip() for line in resume_text.split("\n")
            if any(k in line.lower() for k in ["certificate", "certification", "certified"])
        ]
        role = request.POST.get("role", "").strip() or "Your Role"
        suggested_certs = get_role_based_certifications(role)
        missing_certs = [cert for cert in suggested_certs if not any(cert.lower() in ec.lower() for ec in existing_certs)]

        # Suggestions
        all_suggestions = ats_result.get('suggestions', [])
        if len(all_suggestions) > 2:
            all_suggestions = all_suggestions[:2]

        # Store in session
        request.session['resume_results'] = {
            "applicant_name": applicant_name or "N/A",
            "contact_detection": "YES" if has_email else "NO",
            "linkedin_detection": "YES" if has_linkedin else "NO",
            "github_detection": "YES" if has_github else "NO",
            "ats_score": int(ats_score),
            "overall_score_average": int(overall_score_average),
            "overall_grade": ats_result.get('overall_grade', "N/A"),
            "score_breakdown": ats_result.get('sections', {}),
            "suggestions": all_suggestions,
            "detected_links": extracted_links,
            "pie_chart_image": pie_chart_image,
            "missing_certifications": missing_certs,
            "role": role,
            "show_contact_link": bool(all_suggestions),
        }

        # Redirect after POST → avoids recalculation on refresh
        return redirect('analyze_resume')









from django.shortcuts import render
import os
import tempfile
# from .ats_score_non_tech import ats_scoring_for_non_tech , ats_scoring_non_tech_v2 # at top of file
from .utils import *

from .utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_applicant_name,
    extract_github_username,
    extract_leetcode_username,
    calculate_dynamic_ats_score,
    extract_links_from_pdf  # <- Make sure this exists
)


from .ats_score_non_tech import ats_scoring_for_non_tech, ats_scoring_non_tech_v2

import os
import tempfile
from django.shortcuts import render

def analyze_resume_v2(request):
    context = {
        "applicant_name": "N/A",
        "ats_score": 0,
        "overall_score_average": 0,
        "overall_grade": "N/A",
        "score_breakdown": {},
        "suggestions": [],
        "pie_chart_image": None,
        "detected_links": [],
        "error": None,
    }

    if request.method == 'POST' and request.FILES.get('resume'):
        resume_file = request.FILES['resume']
        ext = os.path.splitext(resume_file.name)[1].lower()

        # Save uploaded file to a temporary path
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            for chunk in resume_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        # Check file format
        if ext not in [".pdf", ".docx", ".doc"]:
            context["error"] = "Unsupported file format. Please upload a PDF, DOCX, or DOC file."
            return render(request, 'score_of_non_tech.html', context)

        # Extract resume text & links
        if ext == ".pdf":
            extracted_links, resume_text = extract_links_combined(temp_path)
        elif ext == ".docx":
            resume_text = extract_text_from_docx(temp_path)
            extracted_links = []
        else:  # .doc
            resume_text = extract_text_from_doc(temp_path)
            extracted_links = []

        # Try to detect applicant name
        applicant_name = extract_applicant_name(resume_text) or "N/A"

        # Run ATS scoring (handles breakdown and average calculation internally)
        ats_result = ats_scoring_non_tech_v2(temp_path)

        # Merge ATS results into context
        context.update({
            "applicant_name": ats_result.get("applicant_name", applicant_name),
            "contact_detection": ats_result.get("contact_detection", "NO"),
            "linkedin_detection": ats_result.get("linkedin_detection", "NO"),
            "github_detection": ats_result.get("github_detection", "NO"),
            "ats_score": ats_result.get("overall_score_average", 0),
            "overall_score_average": ats_result.get("overall_score_average", 0),
            "overall_grade": ats_result.get("overall_grade", "N/A"),
            "score_breakdown": ats_result.get("score_breakdown", {}),
            "pie_chart_image": ats_result.get("pie_chart_image"),
            "suggestions": ats_result.get("suggestions", []),
            "detected_links": extracted_links,
        })

    return render(request, 'score_of_non_tech.html', context)





# --- Profile Building & Payment Views ---
def profile_building(request):
    """
    Renders the Profile Building page with subscription plans.
    """
    return render(request, 'subscription_plans.html')

def payment_instructions(request, plan_id):
    """
    Displays payment instructions with a QR code for the selected plan.
    """
    plan = PLANS.get(plan_id)
    if not plan:
        return redirect('profile_building')

    qr_code_url = "https://placehold.co/200x200/000000/FFFFFF?text=Scan+to+Pay"
    
    context = {
        'plan': plan,
        'qr_code_url': qr_code_url,
    }
    return render(request, 'payment_instructions.html', context)

def submit_payment_details(request):
    """
    Handles the form for submitting payment details and resume,
    and attempts to verify the transaction.
    """
    plan_id_get = request.GET.get('plan_id')

    if request.method == 'POST':
        form = PaymentDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            utr_number = form.cleaned_data['utr_number']
            transaction_screenshot = form.cleaned_data['transaction_screenshot']
            resume = form.cleaned_data['resume']
            plan_id_post = form.cleaned_data.get('plan_id')
            
            plan = PLANS.get(plan_id_post) if plan_id_post else None
            expected_amount = plan['price'] if plan else 0

            # This is where the manual verification logic would be
            submission_dir = os.path.join(settings.MEDIA_ROOT, 'submissions', utr_number)
            os.makedirs(submission_dir, exist_ok=True)

            with open(os.path.join(submission_dir, transaction_screenshot.name), 'wb+') as destination:
                for chunk in transaction_screenshot.chunks():
                    destination.write(chunk)
            
            with open(os.path.join(submission_dir, resume.name), 'wb+') as destination:
                for chunk in resume.chunks():
                    destination.write(chunk)
            
            return redirect('payment_submission_success')
        else:
            if plan_id_get:
                form = PaymentDetailsForm(request.POST, request.FILES, initial={'plan_id': plan_id_get})
            else:
                form = PaymentDetailsForm(request.POST, request.FILES)

            return render(request, 'payment_form.html', {'form': form})
    else: # GET request
        if plan_id_get:
            form = PaymentDetailsForm(initial={'plan_id': plan_id_get})
        else:
            form = PaymentDetailsForm()
    
    return render(request, 'payment_form.html', {'form': form})

def payment_submission_success(request):
    """
    Renders a success page after the payment details form is submitted.
    """
    return render(request, 'payment_submission_success.html')


