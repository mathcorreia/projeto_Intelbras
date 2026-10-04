import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Tenta ler a variável DATABASE_URL do ambiente (Docker).
# Se não encontrar, usa SQLite local como fallback (ideal para testes locais sem Docker).
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./dashboard_data.db"
)

# Verifica se é SQLite para adicionar o argumento específico "check_same_thread"
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Configuração para PostgreSQL (Docker)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()