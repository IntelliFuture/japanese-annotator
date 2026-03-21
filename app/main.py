from fastapi import FastAPI

from app.annotator import Annotator
from app.models import (
    AnnotateRequest,
    AnnotateResponse,
    BatchAnnotateRequest,
    BatchAnnotateResponse,
    HealthResponse,
    NormalizeRequest,
    NormalizeResponse,
    ReloadResponse,
)
from app.normalizer import normalize

app = FastAPI(title="Japanese Annotator", version="1.0.0")
annotator = Annotator()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/normalize", response_model=NormalizeResponse)
def normalize_text(req: NormalizeRequest) -> NormalizeResponse:
    return NormalizeResponse(original=req.text, normalized=normalize(req.text))


@app.post("/annotate", response_model=AnnotateResponse)
def annotate(req: AnnotateRequest) -> AnnotateResponse:
    text = normalize(req.text) if req.pre_normalize else req.text
    return annotator.annotate(text, req.mode)


@app.post("/annotate/batch", response_model=BatchAnnotateResponse)
def annotate_batch(req: BatchAnnotateRequest) -> BatchAnnotateResponse:
    texts = [normalize(t) for t in req.texts] if req.pre_normalize else req.texts
    results = [annotator.annotate(t, req.mode) for t in texts]
    return BatchAnnotateResponse(results=results)


@app.post("/dict/reload", response_model=ReloadResponse)
def dict_reload() -> ReloadResponse:
    annotator.reload_dict()
    return ReloadResponse(status="ok", message="Dictionary reloaded successfully")
