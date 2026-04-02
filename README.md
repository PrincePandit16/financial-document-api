# Financial Document Management API

## Setup
```bash
pip install -r requirements.txt
uvicorn main:app --reload
# Swagger UI → http://localhost:8000/docs
```

## Free Tools Used
- FastAPI + SQLite (relational DB)
- Qdrant in-memory (vector DB)
- sentence-transformers all-MiniLM-L6-v2 (embeddings, local)
- LangChain text splitter (chunking)
- rank-bm25 (reranking)
- JWT (python-jose)

## Endpoints

### Auth
- POST /auth/register
- POST /auth/login

### Documents
- POST /documents/upload
- GET  /documents
- GET  /documents/{document_id}
- DELETE /documents/{document_id}
- GET  /documents/search?title=&company_name=&document_type=

### Roles
- POST /roles/create
- POST /users/assign-role
- GET  /users/{id}/roles
- GET  /users/{id}/permissions

### RAG
- POST /rag/index-document?document_id=
- DELETE /rag/remove-document/{document_id}
- POST /rag/search  {"query": "..."}
- GET  /rag/context/{document_id}

## RAG Pipeline
```
Document → Text Extraction → Chunking → Embeddings → Qdrant
Query → Embedding → Vector Search (top 20) → BM25 Rerank → Top 5
```

## Default Roles (auto-seeded)
| Role | Permissions |
|------|-------------|
| Admin | upload, edit, delete, view, manage_users, manage_roles |
| Financial Analyst | upload, edit, view |
| Auditor | view, review |
| Client | view |
