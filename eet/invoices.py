from . import binding, types
from datetime import datetime
import uuid

from pathlib import Path
import urllib.request
import shutil

from cryptography import x509
from cryptography.x509 import Certificate, oid
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class Config:

    PRODUCTION_URL = "https://www.etrzby.cz/assets/cs/prilohy/cacert-produkcni.crt"
    PRODUCTION_FILE = "production.pem"
    PLAYGROUND_URL = "https://www.etrzby.cz/assets/cs/prilohy/cacert-playground.crt"
    PLAYGROUND_FILE = "playground.pem"

    LOCAL_PATH = str(Path(__file__).parent.absolute().joinpath('certs'))

    def __init__(
        self,
        cert: Certificate,
        private_key: RSAPrivateKey,
        id_provoz: types.IdProvozType,
        id_pokl: types.string20,
        mode: str = "play",
        dic_poverujiciho: types.CZDICType = None
    ):
        if not isinstance(cert, Certificate):
            raise ValueError("invalid certificate")
        self._cert = cert

        subject = self._cert.subject.get_attributes_for_oid(oid.NameOID.COMMON_NAME)[0].value

        self._val = {
            "dic_popl": types.CZDICType(subject),
            "id_provoz": types.IdProvozType(id_provoz),
            "id_pokl": types.string20(id_pokl),
        }
        
        if mode != "prod" and mode != "play":
            raise ValueError("invalid mode must be one of {\"prod\", \"play\"}")
        self._mode = mode

        if dic_poverujiciho:
            self._val["dic_poverujiciho"] = types.CZDICType(dic_poverujiciho)
        

        if not isinstance(private_key, RSAPrivateKey):
            raise ValueError("invalid private key")
        self._private_key = private_key

        if self._mode == "play":
            self._root_cert = self.__load_or_download(self.PLAYGROUND_FILE, self.PLAYGROUND_URL)
        else:
            self._root_cert = self.__load_or_download(self.PRODUCTION_FILE, self.PRODUCTION_URL)
    
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
    
    def root_cert(self):
        return self._root_cert
    
    def private_key(self):
        return self._private_key
    
    @staticmethod
    def __load_or_download(filename: str, url: str):
        path = Path(Config.LOCAL_PATH).joinpath(filename)

        try:
            if path.is_file():
                try:
                    cert = Config.__load_cert(str(path))
                    if not Config.__check_validity(cert):
                        Config.__download(str(path), url)
                        cert = Config.__load_cert(str(path))
                except ValueError:
                    Config.__download(str(path), url)
                    cert = Config.__load_cert(str(path))
            else:
                Config.__download(str(path), url)
                cert = Config.__load_cert(str(path))
        except ValueError:
            raise ValueError("Failed to load certificate. Check internet connection")
        
        if not Config.__check_validity(cert):
            raise ValueError("Certificate expired. Check system time")

        return cert
    
    @staticmethod
    def __check_validity(cert: Certificate):
        now = datetime.utcnow()
        if cert.not_valid_before > now or cert.not_valid_after < now:
            return False
        return True

    @staticmethod
    def __load_cert(filename: str):
        cert_file = open(filename, 'rb')
        key = cert_file.read().strip()
        cert_file.close()
        return x509.load_pem_x509_certificate(key, default_backend())
    
    @staticmethod
    def __download(filename: str, url: str):
        with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

class Invoice(binding.Trzba):
    
    def __init__(self, cert: Certificate, private_key: RSAPrivateKey):
        super()
        self._cert = cert
        self._private_key = private_key

    def _buildXml(self):
        return binding.Soap(self._cert, self._private_key).build(self)
    
    def send(self):
        if self.Hlavicka["prvni_zaslani"] or not "dat_odesl" in self.Hlavicka:
            self.Hlavicka["dat_odesl"] = types.dateTime.utcnow()
        self.Hlavicka["uuid_zpravy"] = types.UUIDType(str(uuid.uuid4()))

        print(self._buildXml())
        

class Factory:
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
        sale = Invoice(self._config.cert(), self._config.private_key())
        
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
