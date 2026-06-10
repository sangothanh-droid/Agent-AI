"""
Backend FastAPI — Agent IA Personnel
Avec historique Supabase, projets et recherche
"""
import os
import threading
import time
import logging
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from agent import Agent
import database as db

load_dotenv()

app = FastAPI(title="Agent IA Personnel")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Keep-alive (anti-sleep Render) ──
def _keep_alive():
    url = os.getenv("RENDER_URL", "https://agent-ai-1r9d.onrender.com")
    interval = 600  # 10 minutes
    time.sleep(30)  # attend que le serveur soit bien démarré
    while True:
        try:
            r = requests.get(url, timeout=10)
            logging.info(f"[keep-alive] ping OK — {r.status_code}")
        except Exception as e:
            logging.warning(f"[keep-alive] ping échoué : {e}")
        time.sleep(interval)

threading.Thread(target=_keep_alive, daemon=True).start()

# Sessions en mémoire (agent + historique actif)
sessions: dict[str, Agent] = {}

# ── Modèles ──
class ChatRequest(BaseModel):
    conversation_id: str
    message: str

class CreateProjectRequest(BaseModel):
    name: str

class CreateConversationRequest(BaseModel):
    title: str
    project_id: Optional[str] = None

class RenameRequest(BaseModel):
    title: str

# ── Health ──
@app.get("/")
def root():
    return {"status": "ok", "message": "Agent IA en ligne 🤖"}

# ── Projets ──
@app.get("/projects")
def list_projects():
    return db.get_projects()

@app.post("/projects")
def create_project(req: CreateProjectRequest):
    project = db.create_project(req.name)
    if not project:
        raise HTTPException(status_code=500, detail="Erreur création projet")
    return project

@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    db.delete_project(project_id)
    return {"status": "ok"}

# ── Conversations ──
@app.get("/conversations")
def list_conversations(project_id: Optional[str] = None):
    return db.get_conversations(project_id)

@app.post("/conversations")
def create_conversation(req: CreateConversationRequest):
    conv = db.create_conversation(req.title, req.project_id)
    if not conv:
        raise HTTPException(status_code=500, detail="Erreur création conversation")
    return conv

@app.patch("/conversations/{conv_id}")
def rename_conversation(conv_id: str, req: RenameRequest):
    db.update_conversation_title(conv_id, req.title)
    return {"status": "ok"}

@app.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    db.delete_conversation(conv_id)
    if conv_id in sessions:
        del sessions[conv_id]
    return {"status": "ok"}

@app.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: str):
    return db.get_messages(conv_id)

# ── Chat ──
@app.post("/chat")
def chat(req: ChatRequest):
    import traceback
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY manquante")
    if req.conversation_id not in sessions:
        sessions[req.conversation_id] = Agent()
        messages = db.get_messages(req.conversation_id)
        for m in messages:
            if m["role"] in ("user", "assistant"):
                sessions[req.conversation_id].history.append({
                    "role": m["role"],
                    "content": m["content"]
                })
    agent = sessions[req.conversation_id]
    db.save_message(req.conversation_id, "user", req.message)
    try:
        response = agent.chat(req.message)
    except Exception as e:
        detail = traceback.format_exc()
        print(f"ERREUR CHAT: {detail}")
        raise HTTPException(status_code=500, detail=str(e))
    db.save_message(req.conversation_id, "assistant", response)
    return {"response": response}

# ── Recherche ──
@app.get("/search")
def search(q: str):
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Requête trop courte")
    return db.search_messages(q)
