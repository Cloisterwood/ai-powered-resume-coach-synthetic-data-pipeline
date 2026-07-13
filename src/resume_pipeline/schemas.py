"""Strict schemas. All spec validation rules live here, nowhere else."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

Proficiency = Literal["Beginner", "Intermediate", "Advanced", "Expert"]
ExperienceLevel = Literal["Entry", "Mid", "Senior", "Lead", "Executive"]
FitLevel = Literal["excellent", "good", "partial", "poor", "mismatch"]
TemplateName = Literal[
    "formal", "casual", "technical", "achievement", "career_changer"
]

SENIORITY_RANK: dict[str, int] = {
    "Entry": 0,
    "Mid": 1,
    "Senior": 2,
    "Lead": 3,
    "Executive": 4,
}


class ContactInfo(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    phone: str = Field(min_length=10)
    location: str = Field(min_length=1)
    linkedin: str | None = None
    portfolio: str | None = None


class Education(BaseModel):
    degree: str = Field(min_length=1)
    institution: str = Field(min_length=1)
    graduation_date: date
    gpa: float | None = Field(default=None, ge=0.0, le=4.0)
    coursework: list[str] | None = None


class Experience(BaseModel):
    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    start_date: date
    end_date: date | None = None
    responsibilities: list[str]
    achievements: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def end_after_start(self) -> "Experience":
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class Skill(BaseModel):
    name: str = Field(min_length=1)
    proficiency_level: Proficiency
    years: float | None = Field(default=None, ge=0, le=50)


class ResumeMetadata(BaseModel):
    trace_id: str
    generated_at: datetime
    prompt_template: TemplateName
    fit_level: FitLevel
    writing_style: str


class Resume(BaseModel):
    contact: ContactInfo
    summary: str | None = None
    education: list[Education] = Field(min_length=1)
    experience: list[Experience]
    skills: list[Skill] = Field(min_length=1)
    metadata: ResumeMetadata


class CompanyInfo(BaseModel):
    name: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    size: str = Field(min_length=1)
    location: str = Field(min_length=1)


class JobMetadata(BaseModel):
    trace_id: str
    generated_at: datetime
    is_niche_role: bool


class JobDescription(BaseModel):
    title: str = Field(min_length=1)
    company: CompanyInfo
    description: str = Field(min_length=1)
    required_skills: list[str] = Field(min_length=1)
    preferred_skills: list[str] = Field(default_factory=list)
    education: str
    experience_years: int = Field(ge=0, le=30)
    experience_level: ExperienceLevel
    metadata: JobMetadata


class ResumePair(BaseModel):
    pair_id: str
    job_trace_id: str
    resume_trace_id: str
    fit_level: FitLevel
    prompt_template: TemplateName
    is_niche_role: bool
    generated_at: datetime
