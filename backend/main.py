import os
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from database import get_documents, delete_document
from ingestion import process_document
from retrieval import hybrid_search
from generation import generate_response_sse
from endee_client import endee_client

app = FastAPI(title="DocuMind Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.environ.get("DATA_DIR", "./data")

class QueryRequest(BaseModel):
    query: str

@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(DATA_DIR, f"{doc_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    background_tasks.add_task(process_document, file_path, file.filename, doc_id)
    return {"id": doc_id, "filename": file.filename, "status": "processing"}

@app.post("/api/query")
async def query_documents(req: QueryRequest):
    chunks = hybrid_search(req.query, final_top_k=5)
    if not chunks:
        async def empty_stream():
            yield "data: {\"content\": \"No relevant documents found. Please upload documents first.\"}\n\n"
            yield "data: {\"done\": true}\n\n"
        return StreamingResponse(empty_stream(), media_type="text/event-stream")
        
    return StreamingResponse(
        generate_response_sse(req.query, chunks),
        media_type="text/event-stream"
    )

@app.get("/api/documents")
def list_documents():
    return get_documents()

@app.delete("/api/document/{doc_id}")
def remove_document(doc_id: str):
    delete_document(doc_id)
    endee_client.delete_by_filter(doc_id)
    return {"status": "deleted"}

@app.get("/api/health")
def health_check():
    endee_stats = endee_client.get_stats()
    return {"status": "ok", "endee": endee_stats}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
