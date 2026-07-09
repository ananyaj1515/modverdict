from datetime import datetime
from typing import List, Optional
from sqlmodel import Column, Field, SQLModel
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

class Reviews(SQLModel, table=True):
    id: int = Field(primary_key=True)
    course_code: str = Field(max_length=10, nullable=False)
    raw_message: str = Field(nullable=False)
    created_at: datetime = Field(nullable=False)
    disqus_id: int = Field(nullable=False, unique=True)
    likes: int = Field(default=0, nullable=False)
    parent_disqus_id: int = Field(nullable=True)

class Summary(SQLModel, table=True):
    id: int = Field(primary_key=True)
    course_code: str = Field(max_length=10, nullable=False, unique=True)
    summary: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    praises: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    complaints: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    difficulty: Optional[float] = Field(le=10, nullable=True)
    workload: Optional[float] = Field(le=10, nullable=True)
    enjoyability: Optional[float] = Field(le=10, nullable=True)