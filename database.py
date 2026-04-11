from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não definida nas variáveis de ambiente.")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # verifica conexão antes de usar do pool
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os models."""
    pass


def get_db():
    """
    Gerador para injeção de dependência no FastAPI.
    Garante que a sessão seja fechada após cada request.

    Uso:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
