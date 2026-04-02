from sqlalchemy import create_engine, Column, String, DateTime, Boolean, ForeignKey, Enum as SAEnum, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid, enum

engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def new_id():
    return str(uuid.uuid4())


role_permissions = Table("role_permissions", Base.metadata,
    Column("role_id", String, ForeignKey("roles.id")),
    Column("permission_id", String, ForeignKey("permissions.id")),
)
user_roles = Table("user_roles", Base.metadata,
    Column("user_id", String, ForeignKey("users.id")),
    Column("role_id", String, ForeignKey("roles.id")),
)


class DocumentType(str, enum.Enum):
    invoice = "invoice"
    report = "report"
    contract = "contract"

class Permission(Base):
    __tablename__ = "permissions"
    id   = Column(String, primary_key=True, default=new_id)
    name = Column(String, unique=True, nullable=False)
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class Role(Base):
    __tablename__ = "roles"
    id   = Column(String, primary_key=True, default=new_id)
    name = Column(String, unique=True, nullable=False)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

class User(Base):
    __tablename__ = "users"
    id              = Column(String, primary_key=True, default=new_id)
    username        = Column(String, unique=True, nullable=False)
    email           = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    documents = relationship("Document", back_populates="uploader")

class Document(Base):
    __tablename__ = "documents"
    id            = Column(String, primary_key=True, default=new_id)
    title         = Column(String, nullable=False)
    company_name  = Column(String, nullable=False)
    document_type = Column(SAEnum(DocumentType), nullable=False)
    file_path     = Column(String, nullable=False)
    file_name     = Column(String, nullable=False)
    uploaded_by   = Column(String, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    is_indexed    = Column(Boolean, default=False)
    uploader = relationship("User", back_populates="documents")
