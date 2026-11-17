"""Task Board API.

Endpoints worth knowing about for operations:
  GET /healthz  liveness  -- process is up, no dependencies touched
  GET /readyz   readiness -- database reachable, safe to send traffic
  GET /metrics  Prometheus exposition format
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import engine, get_db, init_db, wait_for_db

logging.basicConfig(
    level=settings.log_level.upper(),
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
log = logging.getLogger("taskboard")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("Starting %s (%s) in %s", settings.app_name, settings.version, settings.environment)
    wait_for_db()
    init_db()
    yield
    log.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="A small task board used to demonstrate a full DevOps pipeline.",
    lifespan=lifespan,
)

if settings.metrics_enabled:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    except ImportError:  # pragma: no cover
        log.warning("prometheus_fastapi_instrumentator not installed; /metrics disabled")


# --------------------------------------------------------------------------
# Operational endpoints
# --------------------------------------------------------------------------
@app.get("/healthz", response_model=schemas.Health, tags=["ops"])
def liveness():
    """Is the process alive? Used by Docker/Kubernetes liveness probes."""
    return schemas.Health(status="ok", version=settings.version, environment=settings.environment)


@app.get("/readyz", tags=["ops"])
def readiness(response: Response):
    """Can we serve traffic? Fails if the database is unreachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "up"}
    except Exception as exc:  # noqa: BLE001
        log.error("Readiness check failed: %s", exc)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not-ready", "database": "down"}


# --------------------------------------------------------------------------
# Task API
# --------------------------------------------------------------------------
@app.get("/api/tasks", response_model=list[schemas.TaskOut], tags=["tasks"])
def list_tasks(db: Session = Depends(get_db), status_filter: str | None = None):
    stmt = select(models.Task).order_by(models.Task.created_at.desc())
    if status_filter:
        stmt = stmt.where(models.Task.status == status_filter)
    return db.scalars(stmt).all()


@app.post(
    "/api/tasks",
    response_model=schemas.TaskOut,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    task = models.Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    log.info("Created task id=%s", task.id)
    return task


@app.get("/api/tasks/{task_id}", response_model=schemas.TaskOut, tags=["tasks"])
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/api/tasks/{task_id}", response_model=schemas.TaskOut, tags=["tasks"])
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/stats", response_model=schemas.Stats, tags=["tasks"])
def stats(db: Session = Depends(get_db)):
    rows = db.execute(select(models.Task.status, func.count()).group_by(models.Task.status)).all()
    counts = {row[0]: row[1] for row in rows}
    return schemas.Stats(
        total=sum(counts.values()),
        todo=counts.get("todo", 0),
        doing=counts.get("doing", 0),
        done=counts.get("done", 0),
    )


# --------------------------------------------------------------------------
# Web UI
# --------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")
