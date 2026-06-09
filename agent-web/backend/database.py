"""
Module Supabase — gestion des projets, conversations et messages
"""

import os
import requests
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")


def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def sb_get(table: str, params: dict = None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.get(url, headers=headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def sb_post(table: str, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.post(url, headers=headers(), json=data, timeout=10)
    r.raise_for_status()
    return r.json()


def sb_patch(table: str, filters: dict, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {k: f"eq.{v}" for k, v in filters.items()}
    r = requests.patch(url, headers=headers(), params=params, json=data, timeout=10)
    r.raise_for_status()
    return r.json()


def sb_delete(table: str, filters: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {k: f"eq.{v}" for k, v in filters.items()}
    r = requests.delete(url, headers=headers(), params=params, timeout=10)
    r.raise_for_status()


# ── Projets ──

def get_projects():
    return sb_get("projects", {"order": "created_at.desc"})

def create_project(name: str):
    result = sb_post("projects", {"name": name})
    return result[0] if result else None

def delete_project(project_id: str):
    sb_delete("projects", {"id": project_id})


# ── Conversations ──

def get_conversations(project_id: str = None):
    params = {"order": "updated_at.desc"}
    if project_id:
        params["project_id"] = f"eq.{project_id}"
    return sb_get("conversations", params)

def create_conversation(title: str, project_id: str = None):
    data = {"title": title}
    if project_id:
        data["project_id"] = project_id
    result = sb_post("conversations", data)
    return result[0] if result else None

def update_conversation_title(conv_id: str, title: str):
    sb_patch("conversations", {"id": conv_id}, {
        "title": title,
        "updated_at": datetime.utcnow().isoformat()
    })

def delete_conversation(conv_id: str):
    sb_delete("conversations", {"id": conv_id})


# ── Messages ──

def get_messages(conv_id: str):
    return sb_get("messages", {
        "conversation_id": f"eq.{conv_id}",
        "order": "created_at.asc"
    })

def save_message(conv_id: str, role: str, content: str):
    result = sb_post("messages", {
        "conversation_id": conv_id,
        "role": role,
        "content": content,
    })
    # Met à jour updated_at de la conversation
    sb_patch("conversations", {"id": conv_id}, {
        "updated_at": datetime.utcnow().isoformat()
    })
    return result[0] if result else None


# ── Recherche full-text ──

def search_messages(query: str):
    url = f"{SUPABASE_URL}/rest/v1/messages"
    params = {
        "select": "id,conversation_id,role,content,created_at",
        "content": f"fts.{query}",
        "order": "created_at.desc",
        "limit": "20",
    }
    r = requests.get(url, headers=headers(), params=params, timeout=10)
    r.raise_for_status()
    results = r.json()

    # Enrichit avec le titre de la conversation
    conv_ids = list({m["conversation_id"] for m in results})
    convs = {}
    for cid in conv_ids:
        try:
            c = sb_get("conversations", {"id": f"eq.{cid}"})
            if c:
                convs[cid] = c[0]
        except Exception:
            pass

    for m in results:
        m["conversation"] = convs.get(m["conversation_id"], {})

    return results
