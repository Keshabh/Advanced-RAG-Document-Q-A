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

def processPdf(pdfs):
    existing_hashes = set()
    if st.session_state.vector_store:
        for doc in st.session_state.vector_store.docstore._dict.values():
            if "pdf_hash" in doc.metadata:
                existing_hashes.add(doc.metadata["pdf_hash"])

    all_texts = []
    all_metadatas = []
    

    # all_new_chunks = []

    for pdf in pdfs:
        pdf_hash = get_pdf_hash(pdf)

        # ---- DUPLICATE CHECK ----
        print(pdf_hash, existing_hashes)
        if pdf_hash in existing_hashes:
            st.warning(f"⚠️ {pdf.name} already processed. Skipping.")
            continue

        # ---- READ PDF ----
        reader = PdfReader(pdf)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_text(full_text)

        # ---- STORE TEXT + METADATA ----
        for chunk in chunks:
            all_texts.append(chunk)
            all_metadatas.append({
                "pdf_hash": pdf_hash,
                "source": pdf.name
            })

    # ---- ADD ONLY NEW CHUNKS ----
    if all_texts:
        if st.session_state.vector_store:
            st.session_state.vector_store.add_texts(all_texts, metadatas=all_metadatas)
        else:
            st.session_state.vector_store = FAISS.from_texts(
                all_texts,
                embedding=embeddings,
                metadatas=all_metadatas
            )

        st.session_state.vector_store.save_local("faiss_index")
        st.success("New PDFs indexed successfully!")
    else:
        st.info("No new documents to process.")

    flag_processed = True
    return st.session_state.vector_store

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