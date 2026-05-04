import hashlib
import re

def hash_text(data):
    #since file is read and is in bytes format, and hashlib needs byte data to convert it into hash
    #but chunks are in text format, which is required to converted into bytes first i.e done using encode utf-8
    if isinstance(data, bytes):
        #generate hash for entire file
        return hashlib.sha256(data).hexdigest()
    #generate hash for chunk
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
