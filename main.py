from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import IntegrationLog
from schemas import ReportCreate, ReportResponse, StatusEnum, TipoAtoEnum


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Cartório Hub API",
    description="API centralizadora para recebimento e auditoria de resultados de atos cartoriais.",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir em produção
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# POST /api/v1/relatorios
# O cartório envia o resultado do ato (SUCESSO ou ERRO) após comunicação
# direta com a plataforma governamental. O Hub apenas recebe e persiste.
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/relatorios",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar resultado de ato cartorial",
    tags=["Relatórios"],
)
def criar_relatorio(report: ReportCreate, db: Session = Depends(get_db)):
    """
    Recebe a notificação de resultado enviada pelo sistema do cartório
    após a conclusão do envio direto ao órgão governamental e persiste
    o log de auditoria no banco de dados.
    """
    log = IntegrationLog(
        cartorio_id=report.cartorio_id,
        tipo_ato=report.tipo_ato.value,
        status=report.status.value,
        payload_enviado=report.payload,
        mensagem_erro=report.mensagem_erro,
    )

    try:
        db.add(log)
        db.commit()
        db.refresh(log)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir log: {exc}",
        )

    return log


# ---------------------------------------------------------------------------
# GET /api/v1/relatorios — listagem com filtros
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/relatorios",
    response_model=list[ReportResponse],
    summary="Listar logs de integração",
    tags=["Relatórios"],
)
def listar_relatorios(
    cartorio_id:   Optional[str]        = Query(None, description="Filtrar por cartório"),
    tipo_ato:      Optional[TipoAtoEnum] = Query(None, description="Filtrar por tipo de ato"),
    filtro_status: Optional[StatusEnum]  = Query(None, alias="status", description="Filtrar por status"),
    limit:         int                   = Query(50, ge=1, le=200),
    offset:        int                   = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(IntegrationLog)

    if cartorio_id:
        query = query.filter(IntegrationLog.cartorio_id == cartorio_id)
    if tipo_ato:
        query = query.filter(IntegrationLog.tipo_ato == tipo_ato.value)
    if filtro_status:
        query = query.filter(IntegrationLog.status == filtro_status.value)

    return query.order_by(IntegrationLog.data_hora.desc()).offset(offset).limit(limit).all()


# ---------------------------------------------------------------------------
# GET /api/v1/relatorios/{id} — detalhe
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/relatorios/{log_id}",
    response_model=ReportResponse,
    summary="Detalhe de um log",
    tags=["Relatórios"],
)
def detalhe_relatorio(log_id: int, db: Session = Depends(get_db)):
    log = db.query(IntegrationLog).filter(IntegrationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Log {log_id} não encontrado.")
    return log


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/resumo — métricas agregadas
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/dashboard/resumo",
    summary="Métricas gerenciais do hub",
    tags=["Dashboard"],
)
def resumo_dashboard(db: Session = Depends(get_db)):
    """
    Retorna métricas consolidadas para alimentar painéis gerenciais.
    """
    total         = db.query(func.count(IntegrationLog.id)).scalar()
    total_sucesso = db.query(func.count(IntegrationLog.id)).filter(IntegrationLog.status == "SUCESSO").scalar()
    total_erro    = db.query(func.count(IntegrationLog.id)).filter(IntegrationLog.status == "ERRO").scalar()
    taxa_sucesso  = round((total_sucesso / total * 100), 1) if total > 0 else 0.0

    por_tipo = (
        db.query(IntegrationLog.tipo_ato, func.count(IntegrationLog.id))
        .group_by(IntegrationLog.tipo_ato)
        .all()
    )

    por_cartorio = (
        db.query(IntegrationLog.cartorio_id, func.count(IntegrationLog.id))
        .group_by(IntegrationLog.cartorio_id)
        .order_by(func.count(IntegrationLog.id).desc())
        .limit(10)
        .all()
    )

    erros_recentes = (
        db.query(IntegrationLog)
        .filter(IntegrationLog.status == "ERRO")
        .order_by(IntegrationLog.data_hora.desc())
        .limit(5)
        .all()
    )

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "totais": {
            "geral":            total,
            "sucesso":          total_sucesso,
            "erro":             total_erro,
            "taxa_sucesso_pct": taxa_sucesso,
        },
        "por_tipo_ato":  {tipo: count for tipo, count in por_tipo},
        "top_cartorios": [{"cartorio_id": c, "total": n} for c, n in por_cartorio],
        "erros_recentes": [
            {
                "id":          e.id,
                "cartorio_id": e.cartorio_id,
                "tipo_ato":    e.tipo_ato,
                "mensagem":    e.mensagem_erro,
                "data_hora":   e.data_hora.isoformat(),
            }
            for e in erros_recentes
        ],
    }
