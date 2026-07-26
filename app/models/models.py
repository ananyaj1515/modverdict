from datetime import datetime
from typing import List, Optional, Dict
from sqlmodel import Column, Field, SQLModel
from sqlalchemy import BigInteger
from sqlalchemy.dialects.postgresql import ARRAY, TEXT, JSONB

class Reviews(SQLModel, table=True):
    id: int = Field(primary_key=True)
    course_code: str = Field(max_length=10, nullable=False)
    raw_message: str = Field(nullable=False)
    created_at: datetime = Field(nullable=False)
    disqus_id: int = Field(sa_column=Column(BigInteger, nullable=False, unique=True))
    likes: int = Field(default=0, nullable=False)
    parent_disqus_id: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))

class Summary(SQLModel, table=True):
    __tablename__ = "summary"
    id: int = Field(primary_key=True)
    course_code: str = Field(max_length=10, nullable=False, unique=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    overall_summary: str = Field(nullable=False)
    difficulty_rating: Optional[float] = Field(le=10, nullable=True)
    workload_rating: Optional[float] = Field(le=10, nullable=True)
    enjoyability_rating: Optional[float] = Field(le=10, nullable=True)
    praises: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    complaints: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    recommendations: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    teaching_comments: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    concepts: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    assessment_comments: Dict[str, str] = Field(default={}, sa_column=Column(JSONB))

    