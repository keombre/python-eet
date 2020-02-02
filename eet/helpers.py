import urllib.request
import shutil
from datetime import datetime

from cryptography import x509
from cryptography.x509 import Certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def _load_file(filename):
    file_h = open(filename, 'rb')
    content = file_h.read().strip()
    file_h.close()
    return content

def load_cert(filename):
    cert = _load_file(filename)
    return parse_cert(cert)

def load_key(filename, password=None):
    key = _load_file(filename)
    return parse_key(key, password)

def parse_cert(content):
    return x509.load_pem_x509_certificate(content, default_backend())

def parse_key(content, password=None):
    return serialization.load_pem_private_key(content, password, default_backend())

def download(filename: str, url: str):
    with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

def _check_validity(cert: Certificate):
    now = datetime.utcnow()
    if cert.not_valid_before > now or cert.not_valid_after < now:
        return False
    return True