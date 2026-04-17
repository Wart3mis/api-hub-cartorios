from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Cartorio, CentralGovernamental, IntegrationLog, TipoAto
from schemas import ReportCreate, ReportResponse, StatusEnum


# ---------------------------------------------------------------------------
# Seed — popula tabelas de apoio na primeira execução
# ---------------------------------------------------------------------------

def _seed(db: Session) -> None:
    """Insere dados iniciais nas tabelas auxiliares se ainda estiverem vazias."""

    if not db.query(Cartorio).first():
        db.add_all([
            Cartorio(codigo="SP-001", nome="1º Cartório de Registro Civil de São Paulo",    municipio="São Paulo",       estado="SP", cnpj="11.222.333/0001-44"),
            Cartorio(codigo="RJ-042", nome="42º Ofício de Notas do Rio de Janeiro",         municipio="Rio de Janeiro",  estado="RJ", cnpj="22.333.444/0001-55"),
            Cartorio(codigo="MG-017", nome="17º Cartório de Registro de Imóveis de BH",     municipio="Belo Horizonte",  estado="MG", cnpj="33.444.555/0001-66"),
            Cartorio(codigo="BA-008", nome="8º Tabelionato de Notas de Salvador",           municipio="Salvador",        estado="BA", cnpj="44.555.666/0001-77"),
            Cartorio(codigo="RS-033", nome="33º Cartório de Registro Civil de Porto Alegre",municipio="Porto Alegre",    estado="RS", cnpj="55.666.777/0001-88"),
            Cartorio(codigo="PR-021", nome="21º Ofício de Registro de Imóveis de Curitiba", municipio="Curitiba",        estado="PR", cnpj="66.777.888/0001-99"),
            Cartorio(codigo="SC-009", nome="9º Cartório de Notas de Florianópolis",         municipio="Florianópolis",   estado="SC", cnpj="77.888.999/0001-00"),
        ])

    if not db.query(CentralGovernamental).first():
        db.add_all([
            CentralGovernamental(nome="e-Notariado",                                    sigla="ENOTARIADO"),
            CentralGovernamental(nome="Central de Informações de Registro Civil",       sigla="CRC"),
            CentralGovernamental(nome="Sistema Nacional de Informações de Reg. Civil",  sigla="SIRC"),
            CentralGovernamental(nome="Operador Nacional do Sist. de Reg. de Imóveis", sigla="ONR"),
        ])

    if not db.query(TipoAto).first():
        db.add_all([
            TipoAto(codigo="NASCIMENTO"),
            TipoAto(codigo="CASAMENTO"),
            TipoAto(codigo="OBITO"),
            TipoAto(codigo="ESCRITURA"),
            TipoAto(codigo="PROCURACAO"),
            TipoAto(codigo="MATRICULA"),
            TipoAto(codigo="REGISTRO"),
        ])

    db.commit()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        _seed(db)
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Cartório Hub API",
    description="API centralizadora para recebimento e auditoria de resultados de atos cartoriais.",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# POST /api/v1/relatorios
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
    # Valida FK de cartório
    if not db.query(Cartorio).filter(Cartorio.id == report.cartorio_id).first():
        raise HTTPException(status_code=404, detail=f"Cartório id={report.cartorio_id} não encontrado.")

    # Valida FK de central
    if not db.query(CentralGovernamental).filter(CentralGovernamental.id == report.central_id).first():
        raise HTTPException(status_code=404, detail=f"Central id={report.central_id} não encontrada.")

    # Valida FK de tipo de ato
    if not db.query(TipoAto).filter(TipoAto.id == report.tipo_ato_id).first():
        raise HTTPException(status_code=404, detail=f"Tipo de ato id={report.tipo_ato_id} não encontrado.")

    log = IntegrationLog(
        cartorio_id=report.cartorio_id,
        central_id=report.central_id,
        tipo_ato_id=report.tipo_ato_id,
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
        raise HTTPException(status_code=500, detail=f"Erro ao persistir log: {exc}")

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
    cartorio_id:   Optional[int]       = Query(None, description="Filtrar por ID do cartório"),
    central_id:    Optional[int]       = Query(None, description="Filtrar por ID da central"),
    tipo_ato_id:   Optional[int]       = Query(None, description="Filtrar por ID do tipo de ato"),
    filtro_status: Optional[StatusEnum] = Query(None, alias="status", description="Filtrar por status"),
    limit:         int                  = Query(50, ge=1, le=200),
    offset:        int                  = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(IntegrationLog)

    if cartorio_id:
        query = query.filter(IntegrationLog.cartorio_id == cartorio_id)
    if central_id:
        query = query.filter(IntegrationLog.central_id == central_id)
    if tipo_ato_id:
        query = query.filter(IntegrationLog.tipo_ato_id == tipo_ato_id)
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
# GET /api/v1/cartorios — lista cartórios cadastrados
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/cartorios",
    summary="Listar cartórios cadastrados",
    tags=["Cadastros"],
)
def listar_cartorios(db: Session = Depends(get_db)):
    return db.query(Cartorio).order_by(Cartorio.codigo).all()


# ---------------------------------------------------------------------------
# GET /api/v1/centrais — lista centrais governamentais
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/centrais",
    summary="Listar centrais governamentais",
    tags=["Cadastros"],
)
def listar_centrais(db: Session = Depends(get_db)):
    return db.query(CentralGovernamental).order_by(CentralGovernamental.sigla).all()


# ---------------------------------------------------------------------------
# GET /api/v1/tipos-ato — lista tipos de ato
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/tipos-ato",
    summary="Listar tipos de ato",
    tags=["Cadastros"],
)
def listar_tipos_ato(db: Session = Depends(get_db)):
    return db.query(TipoAto).order_by(TipoAto.codigo).all()


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/resumo — métricas agregadas
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/dashboard/resumo",
    summary="Métricas gerenciais do hub",
    tags=["Dashboard"],
)
def resumo_dashboard(db: Session = Depends(get_db)):
    total         = db.query(func.count(IntegrationLog.id)).scalar()
    total_sucesso = db.query(func.count(IntegrationLog.id)).filter(IntegrationLog.status == "SUCESSO").scalar()
    total_erro    = db.query(func.count(IntegrationLog.id)).filter(IntegrationLog.status == "ERRO").scalar()
    taxa_sucesso  = round((total_sucesso / total * 100), 1) if total > 0 else 0.0

    por_tipo = (
        db.query(TipoAto.codigo, func.count(IntegrationLog.id))
        .join(IntegrationLog, IntegrationLog.tipo_ato_id == TipoAto.id)
        .group_by(TipoAto.codigo)
        .all()
    )

    por_cartorio = (
        db.query(Cartorio.codigo, func.count(IntegrationLog.id))
        .join(IntegrationLog, IntegrationLog.cartorio_id == Cartorio.id)
        .group_by(Cartorio.codigo)
        .order_by(func.count(IntegrationLog.id).desc())
        .limit(10)
        .all()
    )

    por_central = (
        db.query(CentralGovernamental.sigla, func.count(IntegrationLog.id))
        .join(IntegrationLog, IntegrationLog.central_id == CentralGovernamental.id)
        .group_by(CentralGovernamental.sigla)
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
        "por_tipo_ato":       {tipo: count for tipo, count in por_tipo},
        "por_central":        {sigla: count for sigla, count in por_central},
        "top_cartorios":      [{"cartorio": c, "total": n} for c, n in por_cartorio],
        "erros_recentes": [
            {
                "id":           e.id,
                "cartorio_id":  e.cartorio_id,
                "central_id":   e.central_id,
                "tipo_ato_id":  e.tipo_ato_id,
                "mensagem":     e.mensagem_erro,
                "data_hora":    e.data_hora.isoformat(),
            }
            for e in erros_recentes
        ],
    }
