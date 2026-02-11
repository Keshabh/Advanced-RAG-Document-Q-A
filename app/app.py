import streamlit as st
from core.embeddings import get_embeddings
from core.retriever import retrieve_context
from services.pdf_processor import processPdf
from core.llm import get_llm
from core.prompt import get_prompt
from langchain_community.vectorstores import FAISS
import os
from core.vector_store import load_vector_store

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
    if os.path.exists("faiss_index"):
        #if faiss_index file is present, then it initializes the vector_store with the faiss_index file
        print("Initializing vector_store with faiss_index...")
        st.session_state.vector_store = load_vector_store()
        print("Initalized vector_store with faiss_index successfully!")


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

if pdfs and submit:
    vector_store = st.session_state.get("vector_store")
    st.session_state.vector_store, message = processPdf(pdfs,vector_store)
    if message:
        print(message.keys())
        if "success" in message.keys():
            st.success(message["success"])
        elif "info" in message.keys():
            st.info(message["info"])


if answerButton and input:
    vector_store = st.session_state.vector_store
    if vector_store:
        st.write("Response: ")
        context = retrieve_context(vector_store,input)
        # st.write(context)
        response = get_llm().invoke(get_prompt().format(context=context, input=input))
        st.write(response.content)
    else:
        st.info("No PDF has been processed, Please Process the document first.")