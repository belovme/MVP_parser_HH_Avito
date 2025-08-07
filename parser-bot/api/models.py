# Pydantic/SQLModel модели
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String

class ResumeBase(SQLModel):
    source: str = Field(..., max_length=10)  # hh|avito
    source_id: str = Field(..., max_length=50)
    fio: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=50)
    experience_years: Optional[int] = Field(None)
    position: Optional[str] = Field(None, max_length=100)
    skills: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    salary_expect: Optional[int] = Field(None)
    published_at: Optional[datetime] = Field(None)
    json_raw: dict = Field(default_factory=dict, sa_column=Column(JSON))

class Resume(ResumeBase, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ResumeCreate(ResumeBase):
    pass

class ResumeUpdate(BaseModel):
    fio: Optional[str] = None
    city: Optional[str] = None
    experience_years: Optional[int] = None
    position: Optional[str] = None
    skills: Optional[List[str]] = None
    salary_expect: Optional[int] = None

class Duplicate(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    orig: UUID = Field(foreign_key="resume.id")
    dup: UUID = Field(foreign_key="resume.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ResumeAnalysis(BaseModel):
    resume: Resume
    score: float
    details: str