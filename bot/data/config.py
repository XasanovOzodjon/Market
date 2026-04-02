import os
import sys
import django

# Django loyiha ildizini Python path ga qo'shish
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
ADMINS = settings.TELEGRAM_ADMINS
IP = settings.IP
