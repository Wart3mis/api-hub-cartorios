from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class IntegrationLog(Base):
    """
    Registra cada tentativa de integração realizada pelo hub,
    seja bem-sucedida ou com erro.
    """
    __tablename__ = "integration_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    cartorio_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tipo_ato: Mapped[str] = mapped_column(String(100), nullable=False)

    # Valores esperados: 'SUCESSO' | 'ERRO' | 'PENDENTE'
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    payload_enviado: Mapped[dict] = mapped_column(JSON, nullable=False)
    mensagem_erro: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<IntegrationLog id={self.id} cartorio={self.cartorio_id} "
            f"status={self.status} data={self.data_hora.isoformat()}>"
        )
