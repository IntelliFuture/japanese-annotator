from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SplitModeType = Literal["A", "B", "C", "a", "b", "c"]

MAX_TEXT_LENGTH = 50_000
MAX_BATCH_SIZE = 100


class NormalizeRequest(BaseModel):
    text: str = Field(max_length=MAX_TEXT_LENGTH)


class NormalizeResponse(BaseModel):
    original: str
    normalized: str


class AnnotateRequest(BaseModel):
    text: str = Field(max_length=MAX_TEXT_LENGTH)
    mode: SplitModeType = "C"
    pre_normalize: bool = Field(default=False, description="If true, normalize text before tokenization")


class BatchAnnotateRequest(BaseModel):
    texts: list[str] = Field(max_length=MAX_BATCH_SIZE)
    mode: SplitModeType = "C"
    pre_normalize: bool = Field(default=False, description="If true, normalize texts before tokenization")


class TokenResult(BaseModel):
    surface: str
    reading: str
    lemma: str
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
