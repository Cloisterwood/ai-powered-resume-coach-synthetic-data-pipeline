"""Loose models used only at generation time.

Strict validation happens later in ``validate.py``. Strict generation-time
schemas would cause Instructor to repair imperfect records before the
validation and correction stages can measure or correct them.
"""

from typing import Any

from pydantic import BaseModel


class LooseResume(BaseModel):
    contact: dict[str, Any] | None = None
    summary: str | None = None
    education: list[dict[str, Any]] | None = None
    experience: list[dict[str, Any]] | None = None
    skills: list[dict[str, Any]] | None = None


class LooseJob(BaseModel):
    title: str | None = None
    company: dict[str, Any] | None = None
    description: str | None = None
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    education: str | None = None
    experience_years: Any | None = None
    experience_level: str | None = None
    is_niche_role: bool | None = None
