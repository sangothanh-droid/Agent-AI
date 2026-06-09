"""
Agent core - Boucle ReAct (Reason + Act)
Utilise Groq (gratuit) avec Llama 3.3 70B
"""

import json
import os
import requests
from tools.bash import bash_tool, BASH_SCHEMA
from tools.files import read_file_tool, write_file_tool, READ_FILE_SCHEMA, WRITE_FILE_SCHEMA
from tools.web import web_search_tool, WEB_SEARCH_SCHEMA
from tools.datetime_tool import datetime_tool, DATETIME_SCHEMA

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu es un agent IA personnel qui tourne en local sur la machine de l'utilisateur.
Tu peux l'aider sur :
- Du code (Python, Bash, PowerShell, JS, etc.) — analyser, déboguer, écrire
- Linux/Windows sysadmin — commandes, configs, dépannage
- Ses fichiers locaux — lire, analyser, modifier
- Des recherches web — trouver des infos récentes
- Exécuter des commandes shell directement sur sa machine

Comportement :
- Sois direct et concis. Pas de blabla inutile.
- Utilise les outils dès que c'est pertinent.
- Pour les commandes shell : explique brièvement ce que tu fais avant de lancer.
- Si une commande peut être dangereuse (rm -rf, format, etc.), demande confirmation.
- Réponds en français sauf si on te parle en anglais.
- Pour le code, utilise des blocs markdown avec la syntaxe colorée.
"""

TOOLS_GROQ = [
    {
        "type": "function",
        "function": {
            "name": BASH_SCHEMA["name"],
            "description": BASH_SCHEMA["description"],
            "parameters": BASH_SCHEMA["input_schema"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": READ_FILE_SCHEMA["name"],
            "description": READ_FILE_SCHEMA["description"],
            "parameters": READ_FILE_SCHEMA["input_schema"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": WRITE_FILE_SCHEMA["name"],
            "description": WRITE_FILE_SCHEMA["description"],
            "parameters": WRITE_FILE_SCHEMA["input_schema"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": WEB_SEARCH_SCHEMA["name"],
            "description": WEB_SEARCH_SCHEMA["description"],
            "parameters": WEB_SEARCH_SCHEMA["input_schema"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": DATETIME_SCHEMA["name"],
            "description": DATETIME_SCHEMA["description"],
            "parameters": DATETIME_SCHEMA["input_schema"],
        },
    },
]

TOOL_MAP = {
    "bash": bash_tool,
    "read_file": read_file_tool,
    "write_file": write_file_tool,
    "web_search": web_search_tool,
    "get_datetime": datetime_tool,
}


class Agent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY manquante dans le .env")
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def reset(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _call_groq(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": self.history,
            "tools": TOOLS_GROQ,
            "tool_choice": "auto",
            "max_tokens": 4096,
        }
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            data = self._call_groq()
            choice = data["choices"][0]
            message = choice["message"]
            finish_reason = choice["finish_reason"]

            self.history.append(message)

            # Réponse finale
            if finish_reason == "stop":
                return message.get("content") or "(pas de réponse)"

            # L'agent veut utiliser un outil
            if finish_reason == "tool_calls":
                tool_calls = message.get("tool_calls", [])

                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args = json.loads(tc["function"]["arguments"])
                    tool_fn = TOOL_MAP.get(tool_name)

                    if tool_fn:
                        try:
                            result = tool_fn(**tool_args)
                        except Exception as e:
                            result = f"Erreur {tool_name}: {str(e)}"
                    else:
                        result = f"Outil inconnu: {tool_name}"

                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result),
                    })
            else:
                break

        return "L'agent a terminé de manière inattendue."
