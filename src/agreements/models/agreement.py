import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AgreementType(str, Enum):
    NDA = "NDA"
    SERVICE_AGREEMENT = "ServiceAgreement"
    EMPLOYMENT = "Employment"
    OTHER = "Other"


class AgreementStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class Base(DeclarativeBase):
    pass


class AgreementORM(Base):
    __tablename__ = "agreements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    agreement_type: Mapped[str] = mapped_column(String, nullable=False)
    parties: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default=AgreementStatus.DRAFT)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


# Pydantic schemas

class AgreementCreate(BaseModel):
    title: str
    agreement_type: AgreementType
    parties: list[dict[str, str]] = Field(default_factory=list)
    content: str = ""
    status: AgreementStatus = AgreementStatus.DRAFT
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgreementUpdate(BaseModel):
    title: str | None = None
    agreement_type: AgreementType | None = None
    parties: list[dict[str, str]] | None = None
    content: str | None = None
    status: AgreementStatus | None = None
    metadata: dict[str, Any] | None = None


class AgreementSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    agreement_type: str
    parties: list[dict[str, str]]
    content: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_orm(cls, obj: AgreementORM) -> "AgreementSchema":
        return cls(
            id=obj.id,
            title=obj.title,
            agreement_type=obj.agreement_type,
            parties=obj.parties or [],
            content=obj.content,
            status=obj.status,
            version=obj.version,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            metadata=obj.metadata_ or {},
        )
