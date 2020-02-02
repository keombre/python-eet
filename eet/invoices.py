from . import binding, types
from datetime import datetime

from pathlib import Path
import urllib.request
import shutil

from cryptography import x509
from cryptography.x509 import Certificate
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
        dic_popl: types.CZDICType,
        id_provoz: types.IdProvozType,
        id_pokl: types.string20,
        private_key: RSAPrivateKey,
        mode: str = "play",
        dic_poverujiciho: types.CZDICType = None
    ):
        self._val = {
            "dic_popl": types.CZDICType(dic_popl),
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

        if self._mode == "play":
            self._cert = self.__load_or_download(self.PLAYGROUND_FILE, self.PLAYGROUND_URL)
        else:
            self._cert = self.__load_or_download(self.PRODUCTION_FILE, self.PRODUCTION_URL)
    
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

class Factory:
    def __init__(self, config: Config, ):
        if not isinstance(config, Config):
            raise ValueError("invalid config")
    
