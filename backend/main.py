import os
import shutil
import uuid
import tempfile
import json
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from cloudinary.utils import cloudinary_url

import database, models, auth
from database import engine, SessionLocal
from app.ingestion.pdf_loader import load_pdf
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import create_chunks
from app.retrieval.pinecone_store import PineconeVectorStore
from app.generation.llm import GeminiLLM
from app.services.rag import RAGPipeline
from app.storage.cloudinary_storage import upload_pdf as cloudinary_upload, delete_pdf

# Create tables
models.Base.metadata.create_all(bind=engine)

# ---------- Configuration ----------
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Global Gemini LLM instance (no heavy models)
llm = None

app = FastAPI(title="ResearchLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Pydantic models ----------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[dict]
    cited_sources: List[dict]

# ---------- Helper ----------
def get_llm():
    global llm
    if llm is None:
        llm = GeminiLLM()
    return llm

def reformulate_query(question: str, history: List[dict]) -> str:
    if not history:
        return question
    llm_instance = get_llm()
    history_str = "\n".join(
        [f"{'User' if msg['role']=='user' else 'Assistant'}: {msg['content']}" for msg in history[-6:]]
    )
    prompt = f"""
Given the conversation history and the latest user question, rewrite the question so that it is standalone and does not depend on pronouns or context.

Conversation:
{history_str}

Latest Question: {question}

Standalone Question:
"""
    reformulated = llm_instance.generate(prompt).strip()
    return reformulated or question

# ---------- Health endpoint ----------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------- Authentication endpoints ----------
@app.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(database.get_db)):
    if auth.get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if auth.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = auth.create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
async def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}

# ---------- Workspace endpoints ----------
@app.post("/workspaces", status_code=201)
async def create_workspace(
    name: str = Form(...),
    files: List[UploadFile] = File(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Create workspace
    new_ws = models.Workspace(name=name, user_id=current_user.id)
    db.add(new_ws)
    db.commit()
    db.refresh(new_ws)

    if files:
        temp_files = []
        try:
            for file in files:
                if not file.filename.endswith(".pdf"):
                    continue
                if file.size > MAX_FILE_SIZE:
                    raise HTTPException(413, f"File {file.filename} exceeds size limit")
                suffix = os.path.splitext(file.filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=TEMP_DIR) as tmp:
                    shutil.copyfileobj(file.file, tmp)
                    tmp_path = tmp.name
                temp_files.append((tmp_path, file.filename))

            if temp_files:
                # Upload to Cloudinary and create Document records
                for tmp_path, original_filename in temp_files:
                    public_id = f"user_{current_user.id}/workspace_{new_ws.id}/{uuid.uuid4()}_{original_filename}"
                    try:
                        cloud_response = cloudinary_upload(tmp_path, public_id)
                        cloud_url = cloud_response["secure_url"]
                    except Exception as e:
                        db.delete(new_ws)
                        db.commit()
                        raise HTTPException(500, f"Cloudinary upload failed: {str(e)}")
                    doc = models.Document(
                        workspace_id=new_ws.id,
                        user_id=current_user.id,
                        filename=original_filename,
                        cloudinary_url=cloud_url,
                        public_id=public_id,
                    )
                    db.add(doc)
                db.commit()

                # Process PDFs -> chunks
                all_chunks = []
                document_urls = {}
                for tmp_path, original_filename in temp_files:
                    doc_id = os.path.splitext(original_filename)[0]
                    raw_pages = load_pdf(tmp_path)
                    cleaned_pages = [{"page": p["page"], "text": clean_text(p["text"])} for p in raw_pages]
                    chunks = create_chunks(cleaned_pages, document_id=doc_id)
                    all_chunks.extend(chunks)

                    doc_record = db.query(models.Document).filter(
                        models.Document.workspace_id == new_ws.id,
                        models.Document.filename == original_filename
                    ).first()
                    if doc_record:
                        document_urls[doc_id] = doc_record.cloudinary_url

                # Store in Pinecone (no local embedding needed)
                if all_chunks:
                    pinecone_store = PineconeVectorStore()
                    pinecone_store.add_chunks(
                        all_chunks,
                        workspace_id=new_ws.id,
                        user_id=current_user.id,
                        document_urls=document_urls,
                    )
        finally:
            for p, _ in temp_files:
                if os.path.exists(p):
                    os.unlink(p)

    return {"workspace_id": new_ws.id, "name": new_ws.name}

@app.get("/workspaces")
async def list_workspaces(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    workspaces = db.query(models.Workspace).filter(models.Workspace.user_id == current_user.id).all()
    return [{"id": ws.id, "name": ws.name, "created_at": ws.created_at} for ws in workspaces]

@app.get("/workspaces/{workspace_id}/documents")
async def list_documents(
    workspace_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    workspace = db.query(models.Workspace).filter(
        models.Workspace.id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or not owned by user")
    docs = db.query(models.Document).filter(models.Document.workspace_id == workspace_id).all()
    return [{"id": doc.id, "filename": doc.filename, "url": doc.cloudinary_url} for doc in docs]

@app.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    signed_url, _ = cloudinary_url(doc.public_id, resource_type="raw", secure=True, sign_url=True)
    return {"url": signed_url, "filename": doc.filename}

@app.get("/workspaces/{workspace_id}/messages")
async def get_messages(
    workspace_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    workspace = db.query(models.Workspace).filter(
        models.Workspace.id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or not owned by user")
    messages = db.query(models.Message).filter(
        models.Message.workspace_id == workspace_id
    ).order_by(models.Message.created_at.asc()).all()
    result = []
    for msg in messages:
        sources = []
        if msg.sources:
            try:
                sources = json.loads(msg.sources)
            except:
                sources = []
        result.append({"role": msg.role, "content": msg.content, "sources": sources})
    return result

@app.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    workspace = db.query(models.Workspace).filter(
        models.Workspace.id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or not owned by user")
    documents = db.query(models.Document).filter(models.Document.workspace_id == workspace_id).all()
    for doc in documents:
        try:
            delete_pdf(doc.public_id)
        except:
            pass
    try:
        pinecone_store = PineconeVectorStore()
        pinecone_store.delete_by_workspace(workspace_id)
    except:
        pass
    db.query(models.Message).filter(models.Message.workspace_id == workspace_id).delete()
    for doc in documents:
        db.delete(doc)
    db.delete(workspace)
    db.commit()
    return {"message": "Workspace deleted successfully"}

@app.post("/workspaces/{workspace_id}/ask", response_model=AskResponse)
async def ask_in_workspace(
    workspace_id: str,
    request: AskRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    workspace = db.query(models.Workspace).filter(
        models.Workspace.id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or not owned by user")

    # Fetch history
    messages = db.query(models.Message).filter(
        models.Message.workspace_id == workspace_id
    ).order_by(models.Message.created_at.desc()).limit(10).all()
    history = [{"role": msg.role, "content": msg.content} for msg in reversed(messages)]

    # Save user message
    user_msg = models.Message(workspace_id=workspace_id, role="user", content=request.question)
    db.add(user_msg)
    db.commit()

    llm_instance = get_llm()
    reformulated = reformulate_query(request.question, history)

    pinecone_store = PineconeVectorStore()
    rag = RAGPipeline(pinecone_store, llm_instance)

    result = rag.answer(
        question=reformulated,
        retrieval_k=10,
        final_k=5,
        workspace_id=workspace_id,
        history=history,
    )

    assistant_msg = models.Message(
        workspace_id=workspace_id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(result["cited_sources"])
    )
    db.add(assistant_msg)
    db.commit()

    for i, src in enumerate(result["cited_sources"], start=1):
        src["citation_number"] = i

    return result