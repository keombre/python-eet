# Python EET API
Simple to use and mostly secure (mainly pedantic) API for Czech EET Gate.

![PyPI - License](https://img.shields.io/pypi/l/czech-eet)
![PyPI](https://img.shields.io/pypi/v/czech-eet)

## Installation
```
pip install czech-eet
```

## Usage

### Basic usage with single request
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
# note: if resending, you should set `eet.invoice.Hlavicka["prvni_zaslani"] = eet.types.boolean(False)`
#       or use scheduler ;-)

# now validate response and get fik
codes = response.codes()
if response:
    print("BKP: {0}\nFIK: {1}".format(codes.bkp, codes.fik))
else:
    print("BKP: {0}\nPKP: {1}".format(codes.bkp, codes.pkp))

```

### Example of scheduler
```python
from eet import invoices, helpers, remote

... # prepare invoice as before

# create instance of scheduler
scheduler = remote.Scheduler()

# same as before but now you can resend invoices
response = scheduler.process(invoice)

# call dispatch is reasonable time interval from your mainloop

import time
while True:
    scheduler.dispatch()
    
    time.sleep(60)

```