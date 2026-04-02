import os, uuid, aiofiles
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from contextlib import asynccontextmanager
from fastapi.security import OAuth2PasswordRequestForm

from database import Base, engine, get_db, User, Role, Permission, Document, DocumentType
from auth import hash_password, verify_password, create_token, get_current_user
import rag as rag_engine

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def seed():
    db = Session(bind=engine)
    defaults = {
        "Admin":             ["upload", "edit", "delete", "view", "manage_users", "manage_roles"],
        "Financial Analyst": ["upload", "edit", "view"],
        "Auditor":           ["view", "review"],
        "Client":            ["view"],
    }
    all_perms = set(p for perms in defaults.values() for p in perms)
    pmap = {}
    for name in all_perms:
        p = db.query(Permission).filter_by(name=name).first()
        if not p:
            p = Permission(name=name); db.add(p); db.flush()
        pmap[name] = p
    for role_name, perm_names in defaults.items():
        if not db.query(Role).filter_by(name=role_name).first():
            r = Role(name=role_name, permissions=[pmap[n] for n in perm_names])
            db.add(r)
    db.commit(); db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed()
    yield

app = FastAPI(title="Financial Document Management API", lifespan=lifespan)


class RegisterIn(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    username: str
    password: str

@app.post("/auth/register", tags=["Auth"])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter_by(username=body.username).first():
        raise HTTPException(400, "Username taken")
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(400, "Email taken")
    user = User(username=body.username, email=body.email, hashed_password=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email}

@app.post("/auth/login", tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@app.post("/documents/upload", tags=["Documents"])
async def upload_document(
    title: str = Form(...),
    company_name: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    ext = Path(file.filename).suffix
    save_name = f"{uuid.uuid4()}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    doc = Document(
        title=title, company_name=company_name,
        document_type=document_type, file_path=save_path,
        file_name=file.filename, uploaded_by=current_user.id,
    )
    db.add(doc); db.commit(); db.refresh(doc)
    return _doc_out(doc)

@app.get("/documents", tags=["Documents"])
def get_all_documents(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [_doc_out(d) for d in db.query(Document).all()]

@app.get("/documents/search", tags=["Documents"])
def search_documents(
    title: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    uploaded_by: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Document)
    if title:         q = q.filter(Document.title.ilike(f"%{title}%"))
    if company_name:  q = q.filter(Document.company_name.ilike(f"%{company_name}%"))
    if document_type: q = q.filter(Document.document_type == document_type)
    if uploaded_by:   q = q.filter(Document.uploaded_by == uploaded_by)
    return [_doc_out(d) for d in q.all()]

@app.get("/documents/{document_id}", tags=["Documents"])
def get_document(document_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    return _doc_out(doc)

@app.delete("/documents/{document_id}", tags=["Documents"])
def delete_document(document_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    if os.path.exists(doc.file_path): os.remove(doc.file_path)
    db.delete(doc); db.commit()
    return {"message": "Deleted"}

def _doc_out(doc: Document):
    return {
        "document_id":   doc.id,
        "title":         doc.title,
        "company_name":  doc.company_name,
        "document_type": doc.document_type,
        "uploaded_by":   doc.uploaded_by,
        "created_at":    doc.created_at,
        "is_indexed":    doc.is_indexed,
        "file_name":     doc.file_name,
    }


class RoleCreateIn(BaseModel):
    name: str
    permission_names: list[str] = []

class AssignRoleIn(BaseModel):
    user_id: str
    role_name: str

@app.post("/roles/create", tags=["Roles"])
def create_role(body: RoleCreateIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if db.query(Role).filter_by(name=body.name).first():
        raise HTTPException(400, "Role already exists")
    perms = []
    for name in body.permission_names:
        p = db.query(Permission).filter_by(name=name).first()
        if not p: raise HTTPException(404, f"Permission '{name}' not found")
        perms.append(p)
    role = Role(name=body.name, permissions=perms)
    db.add(role); db.commit(); db.refresh(role)
    return {"id": role.id, "name": role.name, "permissions": [p.name for p in role.permissions]}

@app.post("/users/assign-role", tags=["Roles"])
def assign_role(body: AssignRoleIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    user = db.query(User).filter_by(id=body.user_id).first()
    if not user: raise HTTPException(404, "User not found")
    role = db.query(Role).filter_by(name=body.role_name).first()
    if not role: raise HTTPException(404, f"Role '{body.role_name}' not found")
    if role not in user.roles:
        user.roles.append(role); db.commit()
    return {"message": f"Role '{role.name}' assigned to '{user.username}'"}

@app.get("/users/{user_id}/roles", tags=["Roles"])
def get_user_roles(user_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user: raise HTTPException(404, "User not found")
    return [{"id": r.id, "name": r.name} for r in user.roles]

@app.get("/users/{user_id}/permissions", tags=["Roles"])
def get_user_permissions(user_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user: raise HTTPException(404, "User not found")
    perms = {p.name for r in user.roles for p in r.permissions}
    return list(perms)


class SearchIn(BaseModel):
    query: str

@app.post("/rag/index-document", tags=["RAG"])
def index_document(document_id: str = Query(...), db: Session = Depends(get_db), _=Depends(get_current_user)):
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    try:
        count = rag_engine.index_document(doc.id, doc.file_path, {
            "title": doc.title, "company_name": doc.company_name,
            "document_type": doc.document_type.value,
        })
        doc.is_indexed = True; db.commit()
        return {"document_id": doc.id, "chunks_indexed": count}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.delete("/rag/remove-document/{document_id}", tags=["RAG"])
def remove_document(document_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    rag_engine.remove_document(document_id)
    doc.is_indexed = False; db.commit()
    return {"message": "Embeddings removed"}

@app.post("/rag/search", tags=["RAG"])
def semantic_search(body: SearchIn, _=Depends(get_current_user)):
    """
    Retrieval pipeline:
      Query → Embedding → Vector Search (top 20) → BM25 Reranking → Top 5
    """
    results = rag_engine.search(body.query)
    return {"query": body.query, "results": results}

@app.get("/rag/context/{document_id}", tags=["RAG"])
def get_document_context(document_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    if not doc.is_indexed: raise HTTPException(400, "Document not indexed yet")
    chunks = rag_engine.get_chunks(document_id)
    return {"document_id": document_id, "title": doc.title, "chunks": chunks, "total_chunks": len(chunks)}
