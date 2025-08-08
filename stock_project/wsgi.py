"""
WSGI config for stock_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

# sys.path.append('/home/cp2invexwealth/pythonDir')

# add the virtualenv site-packages path to the sys.path
# sys.path.append('/home/cp2invexwealth/.local/lib/python3.9/site-packages')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #@danish


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_project.settings')
# os.environ["DJANGO_SETTINGS_MODULE"] = "stock_project.settings"
from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
