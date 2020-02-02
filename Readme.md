# Python EET API
Simple binding for Czech EET.

Example usage
-------------
```python
from eet import invoices

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key

cert_text = '''
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
'''

key_text = '''
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
'''

# load certificate
cert = x509.load_pem_x509_certificate(cert_text)

# load private key
pk = serialization.load_pem_private_key(key_text, None, default_backend())

# create config
config = invoices.Config(cert, pk, 141, "1patro-vpravo")

# create factory using config
factory = invoices.Factory(config)

# build new invoice
invoice = factory.new("141-18543-05", 236.00, zakl_dan1=100.0, dan1=21.0)

# and finally get XML (sending will be implemented)
invoice.send()

```