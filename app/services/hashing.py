import hashlib
import re

def hash_text(data):
    if isinstance(data, bytes):
        #generate hash for pdf
        return hashlib.sha256(data).hexdigest()
    #generate hash for text
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
