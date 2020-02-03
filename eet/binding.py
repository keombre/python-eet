from . import types, helpers

from pathlib import Path
from lxml import etree

import re
import base64
import hashlib
import uuid
import textwrap

# Let's stay cryptic
from cryptography.x509 import Certificate, oid
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric import padding

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
    Codes = {
        "pkp": None, # types.PkpType
        "bkp": None # types.BkpType
    }

class Odpoved:
    Hlavicka = {
        "uuid_zpravy": None, # Optional[types.UUIDType]
        "bkp": None, # Optional[types.BkpType]
        "dat_prij": None, # Optional[types.dateTime]
        "dat_odmit": None # Optional[types.dateTime]
    }
    Potvrzeni = {
        "fik": None, # types.FikType
        "test": None # Optional[types.boolean]
    }
    Chyba = {
        "kod": None, # types.KodChybaType
        "test": None, # Optional[types.boolean],
        "text": None # str
    }
    Varovani = {
        "kod_varov": None, # Optional[types.KodVarovType]
        "text": None # str
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

        etree.SubElement(codes, "{http://fs.mfcr.cz/eet/schema/v3}pkp", sale.KontrolniKody["pkp"]).text = sale.Codes["pkp"]
        etree.SubElement(codes, "{http://fs.mfcr.cz/eet/schema/v3}bkp", sale.KontrolniKody["bkp"]).text = sale.Codes["bkp"]

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

    @staticmethod
    def __validate_message(root: etree, ignore_invalid_cert):

        server_cert_text = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken").text
        server_cert = helpers.parse_cert(b"-----BEGIN CERTIFICATE-----\n" + textwrap.fill(server_cert_text, 64).encode() + b"\n-----END CERTIFICATE-----\n")

        if server_cert.subject.get_attributes_for_oid(oid.NameOID.ORGANIZATION_NAME)[0].value != "Česká republika - Generální finanční ředitelství":
            raise ValueError("invalid server certificate")
            
        if not helpers._check_validity(server_cert):
            raise ValueError("server certificate expired")

        if not ignore_invalid_cert:
            # validate signature
            signature = root.find(".//{http://www.w3.org/2000/09/xmldsig#}SignatureValue").text
            signed_info = root.find(".//{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
            signed_text = etree.tostring(signed_info, method='c14n', exclusive=True, with_comments=False)
            server_cert.public_key().verify(base64.b64decode(signature), signed_text, padding.PKCS1v15(), hashes.SHA256())
        
        # validate digest
        body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
        body_text = etree.tostring(body, method='c14n', exclusive=True, with_comments=False)
        digest = base64.b64encode(hashlib.sha256(body_text).digest()).decode()
        if not root.find(".//{http://www.w3.org/2000/09/xmldsig#}DigestValue").text == digest:
            raise ValueError("invalid digest")

        # validate ref
        body_id = body.get("{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id")
        ref_id = root.find(".//{http://www.w3.org/2000/09/xmldsig#}Reference").get("URI")

        if ref_id != "#" + body_id:
            raise ValueError("invalid body ref")

        # validate token
        BinarySecurityToken = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken")
        sec_token = BinarySecurityToken.get("{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id")
        ref_token = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Reference").get("URI")

        if ref_token != "#" + sec_token:
            raise ValueError("invalid security token")

    @staticmethod
    def _convert(data, type):
        if data is not None:
            return type(data)
        return None
    
    @staticmethod
    def parse_response(text: str, ignore_invalid_cert=False):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.XML(text, parser)

        if root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Security") is not None:
            Soap.__validate_message(root, ignore_invalid_cert)
        
        resp = Odpoved()
        header = root.find(".//{http://fs.mfcr.cz/eet/schema/v3}Hlavicka")
        resp.Hlavicka["uuid_zpravy"] = Soap._convert(header.get("uuid_zpravy"), types.UUIDType)
        resp.Hlavicka["bkp"] = Soap._convert(header.get("bkp"), types.BkpType)
        resp.Hlavicka["dat_prij"] = Soap._convert(header.get("dat_prij"), types.dateTime)
        resp.Hlavicka["dat_odmit"] = Soap._convert(header.get("dat_odmit"), types.dateTime)
        
        success = root.find(".//{http://fs.mfcr.cz/eet/schema/v3}Potvrzeni")
        if success is not None:
            resp.Potvrzeni["fik"] = Soap._convert(success.get("fik"), types.FikType)
            resp.Potvrzeni["test"] = Soap._convert(success.get("test"), types.boolean)
        
        error = root.find(".//{http://fs.mfcr.cz/eet/schema/v3}Chyba")
        if error is not None:
            resp.Chyba["kod"] = Soap._convert(error.get("kod"), types.KodChybaType)
            resp.Chyba["test"] = Soap._convert(error.get("test"), types.boolean)
            resp.Chyba["text"] = error.text
        
        warning = root.find(".//{http://fs.mfcr.cz/eet/schema/v3}Varovani")
        if warning is not None:
            resp.Varovani["kod_varov"] = Soap._convert(warning.get("kod_varov"), types.KodVarovType)
            resp.Varovani["text"] = warning.text
        
        return resp
