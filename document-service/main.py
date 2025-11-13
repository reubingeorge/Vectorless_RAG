from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pypdf
import httpx
import os
import uuid

app = FastAPI(title="Document Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ProcessedDocument(BaseModel):
    filename: str
    page_count: int
    total_chars: int
    estimated_tokens: int
    pages: list[dict]

@app.get("/")
async def root():
    return {"service": "Document Service", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "document-service",
        "port": 8001,
        "version": "1.0.0"
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # Extract text from PDF
        reader = pypdf.PdfReader(file_path)
        page_count = len(reader.pages)

        pages = []
        total_chars = 0

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            char_count = len(text)
            total_chars += char_count

            pages.append({
                "page_number": i + 1,
                "text": text,
                "char_count": char_count,
                "estimated_tokens": int(char_count / 4)  # Rough estimate
            })

        # Estimate total tokens
        estimated_tokens = int(total_chars / 4)

        # Store document metadata in storage service
        async with httpx.AsyncClient() as client:
            storage_response = await client.post(
                "http://storage-service:8005/documents",
                json={
                    "filename": file.filename,
                    "file_path": file_path,
                    "size": len(content),
                    "page_count": page_count,
                    "status": "uploaded"
                }
            )

            if storage_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to store document metadata")

            doc_data = storage_response.json()
            doc_id = doc_data["id"]

        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "page_count": page_count,
            "total_chars": total_chars,
            "estimated_tokens": estimated_tokens,
            "status": "processed",
            "message": "Document uploaded and processed successfully"
        }

    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/documents/{doc_id}/extract")
async def extract_document_text(doc_id: int):
    """Extract full text from document"""
    async with httpx.AsyncClient() as client:
        # Get document from storage
        response = await client.get(f"http://storage-service:8005/documents/{doc_id}")

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_data = response.json()
        file_path = doc_data["file_path"]

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")

        # Extract text
        reader = pypdf.PdfReader(file_path)
        pages = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            pages.append({
                "page_number": i + 1,
                "text": text,
                "char_count": len(text)
            })

        return {
            "doc_id": doc_id,
            "filename": doc_data["filename"],
            "page_count": len(pages),
            "pages": pages
        }

@app.get("/documents/{doc_id}/pages/{page_num}")
async def get_page_text(doc_id: int, page_num: int):
    """Get text from specific page"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://storage-service:8005/documents/{doc_id}")

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_data = response.json()
        file_path = doc_data["file_path"]

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")

        reader = pypdf.PdfReader(file_path)

        if page_num < 1 or page_num > len(reader.pages):
            raise HTTPException(status_code=400, detail="Invalid page number")

        page = reader.pages[page_num - 1]
        text = page.extract_text()

        return {
            "doc_id": doc_id,
            "page_number": page_num,
            "text": text,
            "char_count": len(text)
        }
