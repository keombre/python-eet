from dataclasses import dataclass
from . import types
from typing import Optional

import xml.etree.cElementTree as ET

@dataclass
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
            "digest": "SHA256",
            "cipher": "RSA2048",
            "encoding": "base64"
        },
        "bkp": {
            "digest": "SHA1",
            "encoding": "base16"
        }
    }
    Bkp: types.BkpType = None
    Pkp: types.PkpType = None

def buildDataXml(sale: Trzba):

    root = ET.Element("eet:Trzba")

    ET.SubElement(root, "eet:Hlavicka", {k: str(v) for k, v in Trzba.Hlavicka.items() if v is not None})
    ET.SubElement(root, "eet:Data", {k: str(v) for k, v in Trzba.Data.items() if v is not None})

    codes = ET.SubElement(root, "eet:KontrolniKody")
    ET.SubElement(codes, "eet:pkp", sale.KontrolniKody["pkp"]).text = sale.Pkp
    ET.SubElement(codes, "eet:bkp", sale.KontrolniKody["bkp"]).text = sale.Bkp

    return root

def signEnvelope():
    pass

def buildEnvelope(data: ET.Element):
    root = ET.Element("soap:Envelope", {
        "xmlns:soap": "http://www.w3.org/2003/05/soap-envelope/",
        "soap:encodingStyle": "http://www.w3.org/2003/05/soap-encoding"
    })
    header = ET.SubElement(root, "soap:Header")
    body = ET.SubElement(root, "soap:Body")
    body.append(data)
    
    return root

def demo():
    trzba = Trzba()
    trzba.Hlavicka["uuid_zpravy"] = types.UUIDType("e23e5a5a-08d7-4a08-844d-2b6c6b60621d")
    trzba.Hlavicka["dat_odesl"] = types.dateTime.utcnow()
    trzba.Hlavicka["prvni_zaslani"] = types.boolean(True)
    trzba.Hlavicka["overeni"] = types.boolean(False)

    trzba.Pkp = "asdf"

    print(ET.tostring(buildEnvelope(buildDataXml(trzba))))

demo()