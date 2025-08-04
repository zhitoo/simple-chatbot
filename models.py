from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy import Column


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    session_id: UUID = Field(index=True)
    role: str
    content: str = Field(sa_column=Column(TEXT))
    created_at: datetime = Field(default_factory=datetime.utcnow)
