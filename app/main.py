from fastapi import FastAPI

from app.annotator import Annotator
from app.models import (
    AnnotateRequest,
    AnnotateResponse,
    BatchAnnotateRequest,
    BatchAnnotateResponse,
    HealthResponse,
    ReloadResponse,
)

app = FastAPI(title="Japanese Annotator", version="1.0.0")
annotator = Annotator()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/annotate", response_model=AnnotateResponse)
def annotate(req: AnnotateRequest) -> AnnotateResponse:
    return annotator.annotate(req.text, req.mode, req.normalize)


@app.post("/annotate/batch", response_model=BatchAnnotateResponse)
def annotate_batch(req: BatchAnnotateRequest) -> BatchAnnotateResponse:
    results = [annotator.annotate(t, req.mode, req.normalize) for t in req.texts]
    return BatchAnnotateResponse(results=results)


@app.post("/dict/reload", response_model=ReloadResponse)
def dict_reload() -> ReloadResponse:
    annotator.reload_dict()
    return ReloadResponse(status="ok", message="Dictionary reloaded successfully")
