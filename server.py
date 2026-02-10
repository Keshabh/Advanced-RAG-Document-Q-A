#Here will be making a streamlit application where we will be uploading multiple pdf files 
#then we will break it into chunks , apply embeddings to it, and store it in FAISS db.
#take user input, query in the db, pass the reponse from db as a prompt to LLM
#pass prompt, input i.e user query in the LLM application to return the response in a better way
# from pydantic.v1 import BaseModel, ConfigDict
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
# from langchain_core.tools import StructuredTool
import tempfile
import os
import re
import streamlit as st
import hashlib
import re
# import google.generativeai as genai
from langchain_core.prompts import ChatPromptTemplate

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)


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


def get_pdf_hash(pdf_file):
    """
    Generates a hash for a PDF file based on its raw bytes.
    """
    pdf_bytes = pdf_file.read()
    pdf_file.seek(0)  # reset pointer for future reads
    return hashlib.sha256(pdf_bytes).hexdigest()

#when application loads, if vector_store is not present, then it initializes it to None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
    if os.path.exists("faiss_index"):
        #if faiss_index file is present, then it initializes the vector_store with the faiss_index file
        print("initializing vector_store with faiss_index ")
        st.session_state.vector_store = FAISS.load_local(
            "faiss_index",
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("initalized vector_store with faiss_index successfully")


prompt = ChatPromptTemplate.from_template("""
You are a document-grounded AI assistant.

You MUST follow these rules strictly:
1. Answer ONLY using the provided context.
2. Do NOT use any external knowledge.
3. If the answer is not explicitly present in the context, respond with:
   "The document does not contain this information."
4. Do NOT guess, infer, or assume.
5. Keep the answer concise, clear, and factual.

Context (from retrieved document chunks):
--------------------
{context}
--------------------

User Question:
{input}

Instructions for answering:
- If the question asks for an exact value, definition, formula, or number, reproduce it exactly as written in the context.
- If multiple chunks mention the answer, summarize them without adding new information.
- Prefer bullet points when explaining.

Final Answer:
""")



llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

st.subheader("AI Powered Smart PDF Reader")

with st.sidebar:
    st.header("📂 Upload PDFs")
    uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True
        )
    submit = st.button("Process!", key = "process")

pdfs = []
if uploaded_files:
    for file in uploaded_files:
        pdfs.append(file)


input = st.text_input("Ask anything related to the files uploaded..")
answerButton = st.button("Get Answer", key = "getAnswer")

flag_processed = False

def get_pdf_text(pdfs):
    text = ""
    for pdf in pdfs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    return text

def hash_text(data):
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


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


def processPdf(pdfs):
    vector_store = st.session_state.get("vector_store")

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
        if vector_store:
            vector_store.add_texts(all_texts, metadatas=all_metadatas)
        else:
            vector_store = FAISS.from_texts(
                all_texts,
                embedding=embeddings,
                metadatas=all_metadatas
            )

        vector_store.save_local("faiss_index")
        st.success("PDF updated incrementally (no duplication).")
    else:
        st.info("No new content detected.")

    st.session_state.vector_store = vector_store
    return vector_store


if pdfs and submit:
    st.session_state.vector_store = processPdf(pdfs)

def retrieve_context(query: str):
    # Step 1: semantic search
    docs = st.session_state.vector_store.similarity_search(query, k=10)

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


if answerButton and input:
    st.write("Response: ")
    context = retrieve_context(input)
    # st.write(context)
    response = llm.invoke(prompt.format(context=context, input=input))
    st.write(response.content)
