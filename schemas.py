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
# Request — enviado pelo sistema do cartório após comunicação com o órgão
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
        description="Tipo do ato cartorial registrado.",
    )
    status: StatusEnum = Field(
        ...,
        examples=["SUCESSO"],
        description="Resultado do envio ao órgão governamental, informado pelo cartório.",
    )
    payload: dict[str, Any] = Field(
        ...,
        description="Dados do ato em formato JSON.",
    )
    mensagem_erro: str | None = Field(
        default=None,
        description="Mensagem de erro retornada pelo órgão. Obrigatória quando status=ERRO.",
    )
# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------
class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             int
    cartorio_id:    str
    tipo_ato:       TipoAtoEnum
    status:         StatusEnum
    payload_enviado: dict[str, Any]
    mensagem_erro:  str | None = None
    data_hora:      datetime