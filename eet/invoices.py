from . import binding, types, helpers, remote

from datetime import datetime
from pathlib import Path

import uuid
import base64
import hashlib

from cryptography.x509 import Certificate, oid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class Config:

    def __init__(
        self,
        cert: Certificate,
        private_key: RSAPrivateKey,
        id_provoz: types.IdProvozType,
        id_pokl: types.string20,
        dic_poverujiciho: types.CZDICType = None
    ):
        if not isinstance(cert, Certificate):
            raise ValueError("invalid certificate")
        
        if cert.issuer.get_attributes_for_oid(oid.NameOID.ORGANIZATION_NAME)[0].value != "Česká Republika – Generální finanční ředitelství":
            raise ValueError("Certificate was not issued by MFCR")

        if not helpers._check_validity(cert):
            raise ValueError("certificate expired - check system time or update your certificate")
        self._cert = cert

        cert_type = self._cert.issuer.get_attributes_for_oid(oid.NameOID.COMMON_NAME)[0].value
        if "Playground" in cert_type:
            self._mode = "play"
        else:
            self._mode = "prod"

        subject = self._cert.subject.get_attributes_for_oid(oid.NameOID.COMMON_NAME)[0].value
        try:
            dic_popl = types.CZDICType(subject)
        except ValueError:
            raise ValueError("certificate is not valid for EET")

        self._val = {
            "dic_popl": dic_popl,
            "id_provoz": types.IdProvozType(id_provoz),
            "id_pokl": types.string20(id_pokl),
        }

        if dic_poverujiciho:
            self._val["dic_poverujiciho"] = types.CZDICType(dic_poverujiciho)

        if not isinstance(private_key, RSAPrivateKey):
            raise ValueError("invalid private key")
        self._private_key = private_key
    
    def get(self, val):
        if val in self._val:
            return self._val[val]
        else:
            return None
    
    def play(self):
        return self._mode == "play"
    
    def prod(self):
        return self._mode == "prod"
    
    def cert(self):
        return self._cert
    
    def private_key(self):
        return self._private_key


class Factory:

    class Codes:
        bkp: types.BkpType = None
        pkp: types.PkpType = None
        fik: types.FikType = None

    class Invoice(binding.Trzba):
        def __init__(self, config: Config):
            super()
            self._config = config
            self._codes = Factory.Codes()

        def _buildXml(self):
            return binding.Soap(self._config.cert(), self._config.private_key()).build(self)
        
        def _prepare(self):
            if self.Hlavicka["prvni_zaslani"] or not self.Hlavicka["dat_odesl"]:
                self.Hlavicka["dat_odesl"] = types.dateTime.utcnow()
            self.Hlavicka["uuid_zpravy"] = types.UUIDType(str(uuid.uuid4()))

            sign = self._calc_sign()
            self._codes.pkp = self.Codes["pkp"] = types.PkpType(base64.b64encode(sign).decode())
            self._codes.bkp = self.Codes["bkp"] = types.BkpType(self._calc_bkp(sign))
        
        def _calc_sign(self):
            text = "{0}|{1}|{2}|{3}|{4}|{5}".format(
                self.Data["dic_popl"],
                self.Data["id_provoz"],
                self.Data["id_pokl"],
                self.Data["porad_cis"],
                self.Data["dat_trzby"],
                self.Data["celk_trzba"]
            )
            return self._config.private_key().sign(text.encode('utf8'), padding.PKCS1v15(), hashes.SHA256())
        
        @staticmethod
        def _calc_bkp(sign):
            digest = hashlib.sha1(sign).hexdigest()
            return ("{0}-{1}-{2}-{3}-{4}".format(digest[0:8], digest[8:16], digest[16:24], digest[24:32], digest[32:])).upper()
        
        def build(self):
            self._prepare()
            return self._buildXml()

        def send(self):
            return remote.Scheduler.send(self)
        
        def prod(self):
            return self._config.prod()
        
        def codes(self):
            return self._codes
    
    class Response(binding.Odpoved):
        def __init__(self, codes, obj = None):
            if isinstance(obj, binding.Odpoved):
                self.Hlavicka = obj.Hlavicka
                self.Potvrzeni = obj.Potvrzeni
                self.Chyba = obj.Chyba
                self.Varovani = obj.Varovani
            self._codes = codes
            if self:
                self._codes.fik = self.Potvrzeni["fik"]
        
        def __bool__(self):
            return self.Potvrzeni["fik"] is not None
        
        def codes(self):
            return self._codes
            
    def __init__(self, config: Config, ):
        if not isinstance(config, Config):
            raise ValueError("invalid config")
        self._config = config
    
    def new(
        self,
        porad_cis: types.string25,
        celk_trzba: types.CastkaType,
        dat_trzby: types.dateTime = types.dateTime.utcnow(),
        **kwargs: types.CastkaType
    ):
        sale = self.Invoice(self._config)
        
        # set to True for debugging
        sale.Hlavicka["overeni"] = types.boolean(False)

        sale.Hlavicka["prvni_zaslani"] = types.boolean(True)
        sale.Data["dic_popl"] = self._config.get("dic_popl")
        sale.Data["id_provoz"] = self._config.get("id_provoz")
        sale.Data["id_pokl"] = self._config.get("id_pokl")

        if self._config.get("dic_poverujiciho"):
            sale.Data["dic_poverujiciho"] = self._config.get("dic_poverujiciho")

        sale.Data["porad_cis"] = types.string25(porad_cis)
        sale.Data["celk_trzba"] = types.CastkaType(celk_trzba)

        if not isinstance(dat_trzby, types.dateTime):
            raise ValueError("invalid date")
        sale.Data["dat_trzby"] = dat_trzby
        
        sale.Data["rezim"] = types.RezimType(1 if self._config.play() else 0)

        for price in [
            "zakl_nepodl_dph",
            "zakl_dan1",
            "dan1",
            "zakl_dan2",
            "dan2",
            "zakl_dan3",
            "dan3",
            "cest_sluz",
            "pouzit_zboz1",
            "pouzit_zboz2",
            "pouzit_zboz3",
            "urceno_cerp_zuct",
            "cerp_zuct"
        ]:
            if price in kwargs:
                sale.Data[price] = types.CastkaType(kwargs[price])

        return sale
