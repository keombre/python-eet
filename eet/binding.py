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
        "dic_poverujiciho": None, # types.CZDICType,
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
            "encoding": "base64",
            "data": None # types.PkpType
        },
        "bkp": {
            "digest": "SHA1",
            "encoding": "base16",
            "data": None # types.BkpType
        }
    }

def buildXml(sale: Trzba):

    root = ET.Element("eet:Trzba")
    header = ET.SubElement(root, "eet:Hlavicka", {
        "uuid_zpravy": str(sale.Hlavicka["uuid_zpravy"]),
        "dat_odesl": str(sale.Hlavicka["dat_odesl"]),
        "prvni_zaslani": str(sale.Hlavicka["prvni_zaslani"])
    })

    if sale.Hlavicka["overeni"]:
        header.set("overeni", str(sale.Hlavicka["overeni"]))

    return root

def demo():
    trzba = Trzba()
    trzba.Hlavicka["uuid_zpravy"] = types.UUIDType("e23e5a5a-08d7-4a08-844d-2b6c6b60621d")
    trzba.Hlavicka["dat_odesl"] = types.dateTime.utcnow()
    trzba.Hlavicka["prvni_zaslani"] = types.boolean(True)
    trzba.Hlavicka["overeni"] = types.boolean(False)

    print(ET.tostring(buildXml(trzba)))
