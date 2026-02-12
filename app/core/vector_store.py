from core.embeddings import get_embeddings
from langchain_community.vectorstores import FAISS
from config import FAISS_PATH

def load_vector_store():
    return FAISS.load_local(
            FAISS_PATH,
            get_embeddings(),
            allow_dangerous_deserialization=True
        )

def save_vector_store(vector_store, all_texts, all_metadatas):
    if vector_store:
        vector_store.add_texts(all_texts, metadatas=all_metadatas)
    else:
        vector_store = FAISS.from_texts(
            all_texts,
            embedding=get_embeddings(),
            metadatas=all_metadatas
        )
    vector_store.save_local(FAISS_PATH)
    return vector_store
