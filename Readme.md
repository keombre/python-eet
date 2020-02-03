# Python EET API
Simple binding for Czech EET.

Example usage
-------------
```python
from eet import invoices, helpers

cert_text = b'''
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
'''

key_text = b'''
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
'''

# prepare certificate and private key
cert = helpers.parse_cert(cert_text)
pk   = helpers.parse_key(key_text)

# create config
config = invoices.Config(cert, pk, 141, "1patro-vpravo")

# create factory using config
factory = invoices.Factory(config)

# build new invoice & send
invoice = factory.new("141-18543-05", 236.00, zakl_dan1=100.0, dan1=21.0)
response = invoice.send()

# now validate response and get fik
codes = response.codes()
if response:
    print("BKP: {0}\nFIK: {1}".format(codes.bkp, codes.fik))
else:
    print("BKP: {0}\nPKP: {1}".format(codes.bkp, codes.pkp))

```