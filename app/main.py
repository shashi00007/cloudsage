"""
Main FastAPI Application Entry Point for CloudSage.
"""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes.health import router as health_router
from app.routes.aws import router as aws_router
from app.routes.chat import router as chat_router
from app.routes.rag import rag_router
from app.rag.retriever import get_retriever

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly verify/load RAG vector store on startup
    try:
        retriever = get_retriever()
        if retriever.vector_store.count() == 0:
            from app.rag.ingest import build_knowledge_base
            build_knowledge_base(retriever.vector_store, retriever.embedding_model)
    except Exception as e:
        print(f"[CloudSage Startup] Note: RAG auto-initialization exception: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GenAI-Powered Cloud Operations, Knowledge RAG & Cost Intelligence Assistant",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for local cross-origin development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(health_router)  # Expose directly at /health for convenience
app.include_router(aws_router, prefix="/api/aws", tags=["AWS"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(rag_router, prefix="/api/rag", tags=["RAG Knowledge"])

# Mount frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
