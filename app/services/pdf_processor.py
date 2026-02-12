from core.embeddings import get_embeddings
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.hashing import hash_text
from services.chunking import semantic_sections
from core.vector_store import save_vector_store
from langchain_community.vectorstores import FAISS

def processPdf(pdfs, vector_store):
    existing_chunk_hashes = set()
    existing_docs = {}

    if vector_store:
        for k, doc in vector_store.docstore._dict.items():
            ch = doc.metadata.get("chunk_hash")
            if ch:
                existing_chunk_hashes.add(ch)
                existing_docs[ch] = k

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    all_texts = []
    all_metadatas = []
    new_chunk_hashes = set()

    for pdf in pdfs:
        pdf_bytes = pdf.read()
        pdf_hash = hash_text(pdf_bytes)
        pdf.seek(0)

        reader = PdfReader(pdf)
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        sections = semantic_sections(full_text)

        for section in sections:
            chunks = (
                [section]
                if len(section) <= 1200
                else splitter.split_text(section)
            )

            for chunk in chunks:
                chunk_hash = hash_text(chunk)
                new_chunk_hashes.add(chunk_hash)

                if chunk_hash in existing_chunk_hashes:
                    continue

                all_texts.append(chunk)
                all_metadatas.append({
                    "pdf_hash": pdf_hash,
                    "chunk_hash": chunk_hash,
                    "source": pdf.name
                })
    # st.write(all_texts)
    # exit(1)

    # delete stale chunks
    if vector_store:
        stale_ids = [
            k for ch, k in existing_docs.items()
            if ch not in new_chunk_hashes
        ]
        print(stale_ids)

        if stale_ids:
            vector_store.delete(ids=stale_ids)

    # add new chunks
    if all_texts:
        save_vector_store(vector_store, all_texts, all_metadatas)
        message = {"success" : "PDF updated incrementally (no duplication)."}
    else:
        message = {"info" : "No new content detected."}

    return vector_store, message