import hashlib
import re

def hash_text(data):
    if isinstance(data, bytes):
        #generate hash for entire file
        return hashlib.sha256(data).hexdigest()
    #generate hash for chunk
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
