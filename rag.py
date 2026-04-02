from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
import hashlib

COLLECTION = "documents"
DIM = 384
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

_model = None
_client = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_client():
    global _client
    if _client is None:
        _client = QdrantClient(":memory:")
        _client.recreate_collection(COLLECTION, vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))
    return _client


def extract_text(file_path: str) -> str:
    import fitz
    doc = fitz.open(file_path)
    return "\n".join(page.get_text() for page in doc)


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return [c for c in splitter.split_text(text) if len(c.strip()) > 30]


def point_id(doc_id: str, idx: int) -> int:
    return int(hashlib.md5(f"{doc_id}_{idx}".encode()).hexdigest()[:8], 16)


def index_document(doc_id: str, file_path: str, metadata: dict) -> int:
    text   = extract_text(file_path)
    chunks = chunk_text(text)
    vecs   = get_model().encode(chunks).tolist()
    points = [
        PointStruct(id=point_id(doc_id, i), vector=v,
                    payload={"document_id": doc_id, "chunk_index": i, "chunk_text": c, **metadata})
        for i, (c, v) in enumerate(zip(chunks, vecs))
    ]
    get_client().upsert(COLLECTION, points=points)
    return len(points)


def remove_document(doc_id: str):
    get_client().delete(COLLECTION,
        points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]))


def search(query: str, top_k_rerank: int = 5) -> list[dict]:
    q_vec = get_model().encode([query]).tolist()[0]
    hits  = get_client().search(COLLECTION, query_vector=q_vec, limit=20, with_payload=True)
    if not hits:
        return []

    corpus = [h.payload["chunk_text"].lower().split() for h in hits]
    bm25   = BM25Okapi(corpus)
    scores = bm25.get_scores(query.lower().split())
    max_s  = max(scores) or 1.0

    results = []
    for i, h in enumerate(hits):
        combined = 0.7 * h.score + 0.3 * (scores[i] / max_s)
        results.append({**h.payload, "score": round(combined, 4)})

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k_rerank]


def get_chunks(doc_id: str) -> list[str]:
    points, _ = get_client().scroll(COLLECTION,
        scroll_filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]),
        limit=200, with_payload=True)
    points.sort(key=lambda p: p.payload.get("chunk_index", 0))
    return [p.payload["chunk_text"] for p in points]
