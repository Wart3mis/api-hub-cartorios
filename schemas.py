from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TipoAtoEnum(str, Enum):
    NASCIMENTO = "NASCIMENTO"
    CASAMENTO  = "CASAMENTO"
    OBITO      = "OBITO"
    ESCRITURA  = "ESCRITURA"
    PROCURACAO = "PROCURACAO"
    MATRICULA  = "MATRICULA"
    REGISTRO   = "REGISTRO"


class StatusEnum(str, Enum):
    SUCESSO  = "SUCESSO"
    ERRO     = "ERRO"
    PENDENTE = "PENDENTE"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    cartorio_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        examples=["SP-001"],
        description="Identificador único do cartório.",
    )
    tipo_ato: TipoAtoEnum = Field(
        ...,
        examples=["NASCIMENTO"],
        description="Tipo do ato cartorial a ser registrado.",
    )
    payload: dict[str, Any] = Field(
        ...,
        description="Dados brutos do ato em formato JSON.",
    )


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # compatível com ORM objects

    id: int
    cartorio_id: str
    tipo_ato: TipoAtoEnum
    status: StatusEnum
    payload_enviado: dict[str, Any]
    mensagem_erro: str | None = None
    data_hora: datetime
