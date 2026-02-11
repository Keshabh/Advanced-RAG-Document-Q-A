import re

def semantic_sections(text: str):
    """
    Split text by section headers like:
    Abstract, 1 Introduction, 2 Related Work, etc.
    """
    pattern = r"\n(?=(?:Abstract|\d+\s+[A-Z][^\n]{0,50}))"
    sections = re.split(pattern, text)
    merged = []

    buf = ""
    for part in sections:
        if part.strip() in ["Abstract"] or re.match(r"\d+\s+[A-Z]", part.strip()):
            if buf.strip():
                merged.append(buf.strip())
            buf = part
        else:
            buf += "\n" + part

    if buf.strip():
        merged.append(buf.strip())

    return merged