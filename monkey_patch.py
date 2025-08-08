from django.http import request
from django.http.request import split_domain_port

_original_get_host = request.HttpRequest.get_host

def safe_get_host(self):
    host = self.META.get("HTTP_HOST", "")
    if not host:
        host = "127.0.0.1"
    try:
        domain, port = split_domain_port(host)
    except Exception:
        return "127.0.0.1"
    return host

request.HttpRequest.get_host = safe_get_host
