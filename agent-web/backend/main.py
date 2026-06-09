"""
Backend FastAPI — Agent IA Personnel
Déployable sur Render.com (gratuit)
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import Agent

load_dotenv()

app = FastAPI(title="Agent IA Personnel")

# CORS — autorise Netlify + dev local
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Un agent par session (simple, suffit pour usage perso)
sessions: dict[str, Agent] = {}


class MessageRequest(BaseModel):
    session_id: str
    message: str


class MessageResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {"status": "ok", "message": "Agent IA en ligne 🤖"}


@app.post("/chat", response_model=MessageResponse)
def chat(req: MessageRequest):
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY manquante")

    # Crée ou récupère la session
    if req.session_id not in sessions:
        sessions[req.session_id] = Agent()

    agent = sessions[req.session_id]

    try:
        response = agent.chat(req.message)
        return MessageResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
def reset(session_id: str):
    if session_id in sessions:
        sessions[session_id].reset()
    return {"status": "ok"}
