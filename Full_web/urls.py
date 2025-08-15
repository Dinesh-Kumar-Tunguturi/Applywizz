from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils.module_loading import import_string

def health(_req): return HttpResponse("ok")

def lazy_view(dotted):
    def _wrapped(request, *a, **kw):
        return import_string(dotted)(request, *a, **kw)
    return _wrapped

urlpatterns = [
    path("health/", health, name="health"),
    path("", lazy_view("main.views.landing"), name="landing"),
    path("signin/", lazy_view("main.views.signin"), name="signin"),
    path("login/", lazy_view("main.views.login_view"), name="login"),
    path("signup/", lazy_view("main.views.signup"), name="signup"),
    path("about_us/", lazy_view("main.views.about_us"), name="about_us"),
    path("send-signup-otp", lazy_view("main.views.send_signup_otp"), name="send_signup_otp"),
    path("verify-signup-otp", lazy_view("main.views.verify_signup_otp"), name="verify_signup_otp"),
    path("send-email-otp", lazy_view("main.views.send_login_otp"), name="send_email_otp"),
    path("verify-email-otp", lazy_view("main.views.verify_login_otp"), name="verify_email_otp"),
    path("upload_resume/", lazy_view("main.views.upload_resume"), name="upload_resume"),
    path("analyze_resume/", lazy_view("main.views.analyze_resume"), name="analyze_resume"),
    path("analyze_resume_v2/", lazy_view("main.views.analyze_resume_v2"), name="analyze_resume_v2"),
    path("profile_building/", lazy_view("main.views.profile_building"), name="profile_building"),
    path("payment_instructions/<int:plan_id>/", lazy_view("main.views.payment_instructions"), name="payment_instructions"),
    path("submit_payment_details/", lazy_view("main.views.submit_payment_details"), name="submit_payment_details"),
    path("payment_submission_success/", lazy_view("main.views.payment_submission_success"), name="payment_submission_success"),
    path("download_resume_report/", lazy_view("main.views.download_resume_pdf"), name="download_resume_report"),
    path("admin/", admin.site.urls),
]
