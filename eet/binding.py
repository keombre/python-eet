from . import types
from typing import Optional

from pathlib import Path
from lxml import etree

import re
import base64
import hashlib
import uuid

# Let's stay cryptic
from cryptography import x509
from cryptography.x509 import Certificate
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

class Trzba:
    Hlavicka = {
        "uuid_zpravy": None, # types.UUIDType,
        "dat_odesl": None, # types.dateTime,
        "prvni_zaslani": None, # types.boolean,
        "overeni": None # Optional[types.boolean]
    }
    Data = {
        "dic_popl": None, # types.CZDICType,
        "dic_poverujiciho": None, # Optional[types.CZDICType],
        "id_provoz": None, # types.IdProvozType,
        "id_pokl": None, # types.string20,
        "porad_cis": None, # types.string25,
        "dat_trzby": None, # types.dateTime,
        "celk_trzba": None, # types.CastkaType,
        "zakl_nepodl_dph": None, # Optional[types.CastkaType],
        "zakl_dan1": None, # Optional[types.CastkaType],
        "dan1": None, # Optional[types.CastkaType],
        "zakl_dan2": None, # Optional[types.CastkaType],
        "dan2": None, # Optional[types.CastkaType],
        "zakl_dan3": None, # Optional[types.CastkaType],
        "dan3": None, # Optional[types.CastkaType],
        "cest_sluz": None, # Optional[types.CastkaType],
        "pouzit_zboz1": None, # Optional[types.CastkaType],
        "pouzit_zboz2": None, # Optional[types.CastkaType],
        "pouzit_zboz3": None, # Optional[types.CastkaType],
        "urceno_cerp_zuct": None, # Optional[types.CastkaType],
        "cerp_zuct": None, # Optional[types.CastkaType],
        "rezim": None # types.RezimType
    }
    KontrolniKody = {
        "pkp": {
            "digest": "SHA256", # str
            "cipher": "RSA2048", # str
            "encoding": "base64" # str
        },
        "bkp": {
            "digest": "SHA1", # str
            "encoding": "base16" # str
        }
    }

class Soap:

    def __init__(self, cert: Certificate, private_key: RSAPrivateKey):
        if not isinstance(cert, Certificate):
            raise ValueError("cert is not instance of Certificate")
        self.cert = cert

        if not isinstance(private_key, RSAPrivateKey):
            raise ValueError("private_key is not instance of RSAPrivateKey")
        self.private_key = private_key
    
    def __get_cert(self):
        return self.cert.public_bytes(serialization.Encoding.PEM).replace(b"-----BEGIN CERTIFICATE-----", b"").replace(b"-----END CERTIFICATE-----", b"").replace(b"\n", b"")

    def build(self, sale: Trzba):
        return etree.tostring(self._build_envelope(self._build_data_element(sale)))

    def _build_data_element(self, sale: Trzba):
        root = etree.Element("{http://fs.mfcr.cz/eet/schema/v3}Trzba", nsmap={
            None: "http://fs.mfcr.cz/eet/schema/v3",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsd": "http://www.w3.org/2001/XMLSchema"
        })

        etree.SubElement(root, "{http://fs.mfcr.cz/eet/schema/v3}Hlavicka", {k: str(v) for k, v in Trzba.Hlavicka.items() if v is not None})
        etree.SubElement(root, "{http://fs.mfcr.cz/eet/schema/v3}Data", {k: str(v) for k, v in Trzba.Data.items() if v is not None})
        codes = etree.SubElement(root, "{http://fs.mfcr.cz/eet/schema/v3}KontrolniKody")

        sign = self._calc_sign(sale)
        etree.SubElement(codes, "{http://fs.mfcr.cz/eet/schema/v3}pkp", sale.KontrolniKody["pkp"]).text = base64.b64encode(sign)
        etree.SubElement(codes, "{http://fs.mfcr.cz/eet/schema/v3}bkp", sale.KontrolniKody["bkp"]).text = self._calc_bkp(sign)

        return root

    def _build_envelope(self, data: etree.Element):

        binary_token = "X509-" + str(uuid.uuid4())
        uuid_token = "id-" + str(uuid.uuid4())

        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(str(Path(__file__).parent.absolute().joinpath('soap_template.xml')), parser)
        root = tree.getroot()
        
        # add body
        body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
        body.set("{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id", uuid_token)
        body.append(data)

        # add cert
        BinarySecurityToken = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken")
        BinarySecurityToken.set("{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id", binary_token)
        BinarySecurityToken.text = self.__get_cert()

        # cert ref
        root.find(".//{http://www.w3.org/2000/09/xmldsig#}Reference").set("URI", "#" + uuid_token)

        # digest
        body_text = etree.tostring(body, method='c14n', exclusive=True, with_comments=False)
        digest = base64.b64encode(hashlib.sha256(body_text).digest())
        root.find(".//{http://www.w3.org/2000/09/xmldsig#}DigestValue").text = digest

        # header signed
        signed_info = root.find(".//{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        signed_text = etree.tostring(signed_info, method='c14n', exclusive=True, with_comments=False)
        signed_signed = self.private_key.sign(signed_text, padding.PKCS1v15(), hashes.SHA256())
        root.find(".//{http://www.w3.org/2000/09/xmldsig#}SignatureValue").text = base64.b64encode(signed_signed)

        root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Reference").set("URI", "#" + binary_token)
        
        return root
    
    def _calc_sign(self, sale: Trzba):
        text = "{0}|{1}|{2}|{3}|{4}|{5}".format(
            sale.Data["dic_popl"],
            sale.Data["id_provoz"],
            sale.Data["id_pokl"],
            sale.Data["porad_cis"],
            sale.Data["dat_trzby"],
            sale.Data["celk_trzba"]
        )
        return self.private_key.sign(text.encode('utf8'), padding.PKCS1v15(), hashes.SHA256())
    
    def _calc_bkp(self, sign):
        digest = hashlib.sha1(sign).hexdigest()
        return ("{0}-{1}-{2}-{3}-{4}".format(digest[0:8], digest[8:16], digest[16:24], digest[24:32], digest[32:])).upper()
