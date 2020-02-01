from datetime import datetime, timezone
import re

'''
All types specified in http://fs.mfcr.cz/eet/schema/v3
'''

def _pattern(string: str, regex: str):
    pattern = re.compile(regex)
    return pattern.match(string)

class UUIDType(str):
    PATTERN = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"

    def __new__(cls, val):
        if not _pattern(val, cls.PATTERN):
            raise ValueError(str(val) + " does not match pattern")
        if len(val) != 36:
            raise ValueError(str(val) + " is not 36 chars long")
        return str.__new__(cls, val)

class dateTime(datetime):
    def __str__(self):
        return self.replace(tzinfo=timezone.utc).astimezone().replace(microsecond=0).isoformat()

class CZDICType(str):
    PATTERN = "CZ[0-9]{8,10}"

    def __new__(cls, val):
        if not _pattern(val, cls.PATTERN):
            raise ValueError(str(val) + " does not match pattern")
        return str.__new__(cls, val)

class IdProvozType(int):
    def __new__(cls, val):
        if val < 1 or val > 999999:
            raise ValueError(str(val) + " is outside range")
        return int.__new__(cls, val)

class string20(str):
    PATTERN = "[0-9a-zA-Z\.,:;/#\-_ ]{1,20}"

    def __new__(cls, val):
        if not _pattern(val, cls.PATTERN):
            raise ValueError(str(val) + " does not match pattern")
        return str.__new__(cls, val)

class string25(str):
    PATTERN = "[0-9a-zA-Z\.,:;/#\-_ ]{1,25}"

    def __new__(cls, val):
        if not _pattern(val, cls.PATTERN):
            raise ValueError(str(val) + " does not match pattern")
        return str.__new__(cls, val)

class CastkaType(float):
    def __new__(cls, val):
        if not isinstance(val, (int, float)):
            raise ValueError("could not convert " + str(val))
        if val <= -100000000 or val >= 100000000:
            raise ValueError(str(val) + " is outside or range")
        return float.__new__(cls, val)
    
    def __str__(self):
        return "%.2f" % self

class RezimType(int):
    def __new__(cls, val):
        if val != 0 and val != 1:
            raise ValueError(str(val) + " is not valid")
        return float.__new__(cls, val)

class BkpType(str):
    PATTERN = "[0-9a-fA-F]{8}-[0-9a-fA-F]{8}-[0-9a-fA-F]{8}-[0-9a-fA-F]{8}-[0-9a-fA-F]{8}"

    def __new__(cls, val):
        if not _pattern(val, cls.PATTERN):
            raise ValueError(str(val) + " does not match pattern")
        if len(val) != 44:
            raise ValueError(str(val) + " is not 44 chars long")
        return str.__new__(cls, re.sub(r"\s+", "", val))

class FikType(str):
    PATTERN = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}-[0-9a-fA-F]{2}"

    def __new__(cls, val):
        if not _pattern(val, cls.PATTERN):
            raise ValueError(str(val) + " does not match pattern")
        if len(val) != 39:
            raise ValueError(str(val) + " is not 39 chars long")
        return str.__new__(cls, val)
