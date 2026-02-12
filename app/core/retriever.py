import re

def extract_keywords(query: str):
    """
    Extract exact-match friendly keywords:
    - error codes
    - numbers
    - uppercase tokens
    """
    tokens = re.findall(r"[A-Za-z0-9_\-]+", query)
    keywords = [
        t for t in tokens
        if (
            any(c.isdigit() for c in t) or     # numbers / codes
            t.isupper() or                     # ORA, HTTP
            "_" in t                           # snake_case
        )
    ]
    return set(k.lower() for k in keywords)


def retrieve_context(vector_store, query: str):
    # Step 1: semantic search
    docs = vector_store.similarity_search(query, k=10)

    # Step 2: keyword extraction
    query_keywords = extract_keywords(query)
    print("query", query)
    print("query_keywords: ", query_keywords)

    # Step 3: keyword re-ranking / filtering
    ranked_docs = []
    for doc in docs:
        text = doc.page_content.lower()
        score = sum(1 for kw in query_keywords if kw in text)
        ranked_docs.append((score, doc))

    # sort by keyword score (desc)
    ranked_docs.sort(key=lambda x: x[0], reverse=True)
    # fallback-safe: keep semantic order if no keyword hits
    final_docs = [d for s, d in ranked_docs if s > 0] or docs[:3]
    context = "\n\n".join(doc.page_content for doc in final_docs[:3])
    return context