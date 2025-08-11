import random
import re
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client

# OTP Storage (In-memory, not for production)
otp_storage = {}
signup_otp_storage = {}

# Twilio Credentials
account_sid = 'AC87390e14ffc6d5c94efe3ea5e77a937d'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)

# verification = client.verify \
#     .v2 \
#     .services('VA93dc536826c0ab37d7894d8b241f09a2') \
#     .verifications \
#     .create(to='+919494557188', channel='sms')

# print(verification.sid)

@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        mobile = request.POST.get("mobile")
        formatted_number = f"+91{mobile}"
        try:
            client.verify.v2.services(verify_sid).verifications.create(to=formatted_number, channel='sms')
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
            verification_check = client.verify.v2.services(verify_sid).verification_checks.create(to=formatted_number, code=otp)
            if verification_check.status == "approved":
                return JsonResponse({"status": "success", "redirect_url": "/upload_resume"})
            else:
                return JsonResponse({"status": "error", "message": "Invalid OTP. Try again."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error verifying OTP: {str(e)}"})
    return JsonResponse({"status": "error", "message": "Invalid request"})

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