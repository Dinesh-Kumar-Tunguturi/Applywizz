# api/index.py
import os
from asgiref.wsgi import WsgiToAsgi
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Full_web.settings")  # <-- change PROJECT_NAME
from django.core.wsgi import get_wsgi_application

app = WsgiToAsgi(get_wsgi_application())
