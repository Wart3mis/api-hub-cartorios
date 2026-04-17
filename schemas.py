from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StatusEnum(str, Enum):
    SUCESSO  = "SUCESSO"
    ERRO     = "ERRO"


# ---------------------------------------------------------------------------
# Schemas auxiliares — leitura das tabelas de apoio
# ---------------------------------------------------------------------------

class CartorioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:        int
    codigo:    str
    nome:      str
    municipio: str
    estado:    str
    cnpj:      str


class CentralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:    int
    nome:  str
    sigla: str


class TipoAtoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:     int
    codigo: str


# ---------------------------------------------------------------------------
# Request — enviado pelo sistema do cartório com o resultado do ato
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    cartorio_id: int = Field(
        ...,
        description="ID do cartório cadastrado no hub.",
        examples=[1],
    )
    central_id: int = Field(
        ...,
        description="ID da central governamental para a qual o ato foi enviado.",
        examples=[1],
    )
    tipo_ato_id: int = Field(
        ...,
        description="ID do tipo de ato cartorial.",
        examples=[1],
    )
    status: StatusEnum = Field(
        ...,
        description="Resultado do envio ao órgão governamental, informado pelo cartório.",
        examples=["SUCESSO"],
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

    id:              int
    cartorio_id:     int
    central_id:      int
    tipo_ato_id:     int
    status:          StatusEnum
    payload_enviado: dict[str, Any]
    mensagem_erro:   str | None = None
    data_hora:       datetime
