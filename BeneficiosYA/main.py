import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.whatsapp.webhook import router as webhook_router
from app.rag.retriever import build_index
from app.agent.session import get_session, delete_session
from app.agent.chatbot import process_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranque: construir índice RAG
    build_index()
    yield
    # Shutdown: limpieza si necesario


app = FastAPI(
    title="BeneficiosYA AI",
    description="Agente de WhatsApp que orienta a ciudadanos colombianos vulnerables sobre beneficios del gobierno.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas WhatsApp
app.include_router(webhook_router, prefix="/webhook", tags=["WhatsApp Webhook"])


# --- API de prueba (sin necesidad de WhatsApp) ---

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    sisben_aproximado: str | None = None
    beneficios_count: int = 0


@app.post("/chat", response_model=ChatResponse, tags=["Demo API"])
async def chat(req: ChatRequest):
    """
    Endpoint de prueba para interactuar con el agente sin WhatsApp.
    Ideal para desarrollo y demos de la hackathon.
    """
    session = get_session(req.session_id)
    reply = await process_message(session, req.message)
    return ChatResponse(
        reply=reply,
        session_id=req.session_id,
        sisben_aproximado=session.sisben_aproximado,
        beneficios_count=len(session.beneficios_identificados),
    )


@app.delete("/chat/{session_id}", tags=["Demo API"])
async def reset_session(session_id: str):
    """Reinicia la sesión de un usuario."""
    delete_session(session_id)
    return {"message": f"Sesión '{session_id}' reiniciada"}


@app.get("/health", tags=["Sistema"])
async def health():
    return {
        "status": "ok",
        "claude_configurado": settings.has_claude,
        "whatsapp_configurado": settings.has_whatsapp,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
