from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Cartorio(Base):
    """Serventias extrajudiciais cadastradas no hub."""
    __tablename__ = "cartorios"

    id:        Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo:    Mapped[str] = mapped_column(String(20),  nullable=False, unique=True, index=True)
    nome:      Mapped[str] = mapped_column(String(200), nullable=False)
    municipio: Mapped[str] = mapped_column(String(100), nullable=False)
    estado:    Mapped[str] = mapped_column(String(2),   nullable=False)
    cnpj:      Mapped[str] = mapped_column(String(18),  nullable=False, unique=True)

    logs: Mapped[list["IntegrationLog"]] = relationship(back_populates="cartorio")

    def __repr__(self) -> str:
        return f"<Cartorio {self.codigo} — {self.nome}>"


class CentralGovernamental(Base):
    """Plataformas governamentais com as quais os cartórios se integram."""
    __tablename__ = "centrais_governamentais"

    id:    Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome:  Mapped[str] = mapped_column(String(100), nullable=False)
    sigla: Mapped[str] = mapped_column(String(20),  nullable=False, unique=True, index=True)

    logs: Mapped[list["IntegrationLog"]] = relationship(back_populates="central")

    def __repr__(self) -> str:
        return f"<CentralGovernamental {self.sigla}>"


class TipoAto(Base):
    """Tipos de atos cartoriais reconhecidos pelo hub."""
    __tablename__ = "tipos_ato"

    id:     Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    logs: Mapped[list["IntegrationLog"]] = relationship(back_populates="tipo_ato")

    def __repr__(self) -> str:
        return f"<TipoAto {self.codigo}>"


class IntegrationLog(Base):
    """
    Registro centralizado de cada notificação de resultado recebida
    dos sistemas dos cartórios após envio às plataformas governamentais.
    """
    __tablename__ = "integration_logs"

    id:           Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cartorio_id:  Mapped[int] = mapped_column(Integer, ForeignKey("cartorios.id"),              nullable=False, index=True)
    central_id:   Mapped[int] = mapped_column(Integer, ForeignKey("centrais_governamentais.id"), nullable=False, index=True)
    tipo_ato_id:  Mapped[int] = mapped_column(Integer, ForeignKey("tipos_ato.id"),               nullable=False, index=True)

    # Valores: 'SUCESSO' | 'ERRO'
    status:          Mapped[str]        = mapped_column(String(20),  nullable=False)
    payload_enviado: Mapped[dict]       = mapped_column(JSON,        nullable=False)
    mensagem_erro:   Mapped[str | None] = mapped_column(Text,        nullable=True)
    data_hora:       Mapped[datetime]   = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    cartorio:  Mapped["Cartorio"]              = relationship(back_populates="logs")
    central:   Mapped["CentralGovernamental"]  = relationship(back_populates="logs")
    tipo_ato:  Mapped["TipoAto"]               = relationship(back_populates="logs")

    def __repr__(self) -> str:
        return (
            f"<IntegrationLog id={self.id} cartorio_id={self.cartorio_id} "
            f"status={self.status} data={self.data_hora.isoformat()}>"
        )
