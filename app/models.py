from __future__ import annotations

from pydantic import BaseModel, Field


class AnnotateRequest(BaseModel):
    text: str
    mode: str = Field(default="C", pattern="^[ABCabc]$")
    normalize: bool = Field(default=False, description="If true, use normalized_form as display text in ruby_html")


class BatchAnnotateRequest(BaseModel):
    texts: list[str]
    mode: str = Field(default="C", pattern="^[ABCabc]$")
    normalize: bool = Field(default=False, description="If true, use normalized_form as display text in ruby_html")


class TokenResult(BaseModel):
    surface: str
    reading: str
    normalized: str
    pos: str


class AnnotateResponse(BaseModel):
    tokens: list[TokenResult]
    ruby_html: str


class BatchAnnotateResponse(BaseModel):
    results: list[AnnotateResponse]


class HealthResponse(BaseModel):
    status: str = "ok"


class ReloadResponse(BaseModel):
    status: str
    message: str
