# api/index.py
import os, sys, traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Full_web.settings")

try:
    from django.core.asgi import get_asgi_application
    app = get_asgi_application()   # Vercel looks for `app`
except Exception as e:
    print("❌ Django ASGI init failed:", repr(e), file=sys.stderr)
    traceback.print_exc()
    raise
