# 📁 Financial Document Management API

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/Qdrant-FF4500?style=for-the-badge&logo=qdrant&logoColor=white" />
  <img src="https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" />
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black" />
  <img src="https://img.shields.io/badge/Uvicorn-2C2C2C?style=for-the-badge&logo=gunicorn&logoColor=white" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" />
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square" />
  <img src="https://img.shields.io/badge/Made%20with-❤️-red?style=flat-square" />
</p>

---

A production-ready REST API for managing financial documents with AI-powered semantic search capabilities. Built with FastAPI and a complete RAG (Retrieval-Augmented Generation) pipeline using entirely free and open-source tools — no paid APIs required.

---

## 🚀 Live Demo

> Video demonstration available upon request.

---

## ✨ Features

- 🔐 **JWT Authentication** — Secure register/login with bcrypt password hashing and 24-hour token expiry
- 📄 **Document Management** — Upload, retrieve, search, and delete financial documents with full metadata tracking
- 👥 **Role-Based Access Control** — Four roles with granular permissions, auto-seeded on startup
- 🤖 **AI-Powered Semantic Search** — RAG pipeline with hybrid BM25 + vector reranking
- 📊 **Document Types** — Invoices, Reports, and Contracts supported
- ⚡ **Auto Documentation** — Interactive Swagger UI available at `/docs`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | SQLite + SQLAlchemy |
| Vector DB | Qdrant (in-memory) |
| Embeddings | all-MiniLM-L6-v2 (local, no API key needed) |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| Reranking | rank-bm25 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| PDF Parsing | PyMuPDF |

---

## 📋 Prerequisites

- Python 3.10+
- pip
- Virtual environment (recommended)

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/financial-document-api.git
cd financial-document-api
```

### 2. Create and activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
pip install email-validator
```

### 4. Run the server
```bash
uvicorn main:app --reload
```

### 5. Open Swagger UI
```
http://localhost:8000/docs
```

---

## 📡 API Endpoints

### 🔐 Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and get JWT token |

### 📄 Documents

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents/upload` | Upload a financial document |
| `GET` | `/documents` | Retrieve all documents |
| `GET` | `/documents/{document_id}` | Retrieve a specific document |
| `DELETE` | `/documents/{document_id}` | Delete a document |
| `GET` | `/documents/search` | Search documents by metadata |

### 👥 Roles & Permissions

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/roles/create` | Create a new role |
| `POST` | `/users/assign-role` | Assign a role to a user |
| `GET` | `/users/{id}/roles` | Get roles assigned to a user |
| `GET` | `/users/{id}/permissions` | Get all permissions of a user |

### 🤖 RAG (Semantic Search)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/rag/index-document` | Generate embeddings and store in vector DB |
| `DELETE` | `/rag/remove-document/{id}` | Remove document embeddings |
| `POST` | `/rag/search` | Perform semantic search |
| `GET` | `/rag/context/{document_id}` | Retrieve all document chunks |

---

## 📄 Document Metadata Schema
```json
{
  "document_id": "uuid",
  "title": "string",
  "company_name": "string",
  "document_type": "invoice | report | contract",
  "uploaded_by": "user_uuid",
  "created_at": "datetime",
  "is_indexed": "boolean",
  "file_name": "string"
}
```

---

## 👥 Default Roles (Auto-Seeded on Startup)

| Role | Permissions |
|---|---|
| **Admin** | upload, edit, delete, view, manage_users, manage_roles |
| **Financial Analyst** | upload, edit, view |
| **Auditor** | view, review |
| **Client** | view |

---

## 🤖 RAG Pipeline

### Indexing Pipeline
```
PDF Upload
    ↓
Text Extraction (PyMuPDF)
    ↓
Chunking (512 tokens / 64 overlap — LangChain)
    ↓
Embedding (all-MiniLM-L6-v2 — 384 dimensions)
    ↓
Vector Storage (Qdrant)
```

### Retrieval Pipeline
```
User Query
    ↓
Embedding (all-MiniLM-L6-v2)
    ↓
Vector Search — Top 20 results (Qdrant cosine similarity)
    ↓
BM25 Reranking (70% vector score + 30% BM25 score)
    ↓
Top 5 Most Relevant Results
```

### Example Search Request
```json
POST /rag/search
{
  "query": "financial risk related to high debt ratio"
}
```

### Example Search Response
```json
{
  "query": "financial risk related to high debt ratio",
  "results": [
    {
      "document_id": "uuid",
      "title": "Q3 Financial Report",
      "company_name": "Acme Corp",
      "document_type": "report",
      "chunk_text": "The company maintained a net debt position of $142.5 million, representing a debt-to-EBITDA ratio of 1.4x...",
      "score": 0.8923
    }
  ]
}
```

---

## 🔐 Authentication Flow
```
1. POST /auth/register  →  Create account
2. POST /auth/login     →  Get JWT token
3. Add to header        →  Authorization: Bearer <token>
4. Access all endpoints →  Token valid for 24 hours
```

---

## 📁 Project Structure
```
financial-document-api/
│
├── main.py            # FastAPI app, all route handlers
├── auth.py            # JWT creation, password hashing, token validation
├── database.py        # SQLAlchemy models, database setup
├── rag.py             # Embedding, indexing, search, reranking pipeline
├── requirements.txt   # All dependencies
├── README.md          # Project documentation
└── uploads/           # Uploaded PDF files (auto-created)
```

---

## 📦 Dependencies
```txt
fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.30
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.9
pydantic[email]==2.7.1
email-validator
sentence-transformers==3.0.0
qdrant-client==1.9.1
langchain-text-splitters==0.2.2
pymupdf==1.24.5
rank-bm25==0.2.2
aiofiles==23.2.1
```

---

## ⚠️ Known Limitations

- Qdrant runs **in-memory** — embeddings are lost on server restart and documents must be re-indexed
- RBAC permissions are stored and retrievable but **not yet enforced** at the endpoint level
- SQLite is used for simplicity — can be swapped for PostgreSQL for production use

---

## 🔮 Future Improvements

- [ ] Enforce RBAC permissions on protected endpoints
- [ ] Persistent Qdrant storage across restarts
- [ ] PostgreSQL support for production deployments
- [ ] Support for DOCX and Excel file formats
- [ ] Rate limiting and request throttling
- [ ] Docker containerization
- [ ] Unit and integration test coverage

---

## 👨‍💻 Author

**Your Name**
<br/>
📧 kumaprrince16062002@gmail.com
<br/>
🔗 [LinkedIn](https://linkedin.com/in/prince200)
<br/>
🐙 [GitHub](https://github.com/PrincePandit16)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">Built with ❤️ using FastAPI, Qdrant, and Sentence Transformers</p>
