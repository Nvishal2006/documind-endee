import os
import re
from typing import List
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import docx
from database import add_document, update_document_status, insert_chunk, insert_bm25_tokens
from endee_client import endee_client

print("Loading sentence transformer model locally...")
encoder = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded.")

def extract_text(file_path: str, filename: str) -> List[dict]:
    pages = []
    if filename.lower().endswith('.pdf'):
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append({"page": i + 1, "text": text})
    elif filename.lower().endswith('.docx'):
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        pages.append({"page": 1, "text": text})
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            pages.append({"page": 1, "text": f.read()})
    return pages

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    words = re.findall(r'\S+', text)
    chunks = []
    i = 0
    if not words: return []
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
        if i >= len(words):
            break
    return chunks

def tokenize_for_bm25(text: str) -> List[str]:
    return re.findall(r'\b\w+\b', text.lower())

def process_document(file_path: str, filename: str, doc_id: str):
    try:
        pages = extract_text(file_path, filename)
        vectors_to_upsert = []
        
        for p in pages:
            page_num = p["page"]
            text = p["text"]
            chunks = chunk_text(text)
            
            for index, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_p{page_num}_c{index}"
                insert_chunk(chunk_id, doc_id, page_num, index, chunk)
                
                tokens = tokenize_for_bm25(chunk)
                insert_bm25_tokens(doc_id, chunk_id, tokens)
                
                embedding = encoder.encode(chunk).tolist()
                vectors_to_upsert.append({
                    "id": chunk_id,
                    "vector": embedding,
                    "metadata": {
                        "doc_id": doc_id,
                        "page": page_num,
                        "chunk_index": index
                    }
                })
        
        if vectors_to_upsert:
            endee_client.create_collection()
            endee_client.upsert_vectors(vectors_to_upsert)
            
        update_document_status(doc_id, "ready")
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        update_document_status(doc_id, "error")
