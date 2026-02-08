P-11, P-9

Current State:
---------------
1. Document is getting parsed and stored in faiss vector db, and also creates a file for reuse, and upon questioning, LLM is returning the answer.
2. Fine Tunning done by giving better prompt.
3. Faiss index is used if present, so when application loads, vector db is intiialized with faiss_index file.
4. Same file is getting processed twice- so the top 2 chunks retrieved are same,because of duplication. This needs to be solved. Also hash generated for the pdf needs to be saved as meta data in order to comapre it later. (solved)
? what if i change the file name, but content in before and after is same
? what if file name is same, but content has changed a very little, does it duplicate then. since hash is supposed to be different.

pending
--------
2. Hybrid search model =  Semantic + Keyword Search
3. Re-Ranking
4. Separation of different layer in separate files- pdf to text, chunking, vector_store, retrieval, generation, ui
5. Meta data (file name, page no, source)
6. Avoid storing same information again and again
7. For now processing same file is avoided, but what if i change just 1 line during 2nd time procesing the same file, then file will get reprocessed, and retrievd chunks would be duplicated then.


? how does the following work?
from dotenv import load_dotenv
load_dotenv()



*Scenario* Document update (re-process same file twice with minor modification)
1. Problem with chunk hashing
-> Addition of a single word in the file, can shift the chunk boundaries, and most of the chunks can change, and thus, causes data duplication.

? old chunks to be discarded and new modified chunks to be kept, to keep RAG updated.

#in meta_data = {pdf_has:<hash_of_file>, chunk_hash: <hash_of_each_chunk>}


Approach:
1. keep pdf_hash  for file information useful for traceability and deletion.
2. Do paragraph/section based hashing instead of chunk hasing to avoid boundary shifts.
3. If paragraph/section hash is present in existing_hash: skip it, else add it.
4. For deletion of older chunk which is modified now:
hash from old chunk, which is not present in new chunk hash, delete that chunk

