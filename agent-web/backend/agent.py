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

SYSTEM_PROMPT = """Tu es un agent IA personnel. Tu peux aider sur :
- Du code (Python, Bash, PowerShell, JS, etc.) — analyser, déboguer, écrire
- Linux/Windows sysadmin — commandes, configs, dépannage
- Des recherches web — trouver des infos récentes

Règles importantes :
- N'utilise les outils (bash, web_search, etc.) QUE si c'est vraiment nécessaire.
- Pour les questions générales de connaissance (commandes Linux, explications, code), réponds DIRECTEMENT sans utiliser d'outil.
- Réponds toujours en markdown propre.
- Sois direct et concis. Réponds en français sauf si on te parle en anglais."""

TOOLS_GROQ = [
    {"type": "function", "function": {"name": BASH_SCHEMA["name"], "description": BASH_SCHEMA["description"], "parameters": BASH_SCHEMA["input_schema"]}},
    {"type": "function", "function": {"name": READ_FILE_SCHEMA["name"], "description": READ_FILE_SCHEMA["description"], "parameters": READ_FILE_SCHEMA["input_schema"]}},
    {"type": "function", "function": {"name": WRITE_FILE_SCHEMA["name"], "description": WRITE_FILE_SCHEMA["description"], "parameters": WRITE_FILE_SCHEMA["input_schema"]}},
    {"type": "function", "function": {"name": WEB_SEARCH_SCHEMA["name"], "description": WEB_SEARCH_SCHEMA["description"], "parameters": WEB_SEARCH_SCHEMA["input_schema"]}},
    {"type": "function", "function": {"name": DATETIME_SCHEMA["name"], "description": DATETIME_SCHEMA["description"], "parameters": DATETIME_SCHEMA["input_schema"]}},
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
        self.history = []

    def reset(self):
        self.history = []

    def _call_groq(self, use_tools=True):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history
        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": 4096,
        }
        if use_tools:
            payload["tools"] = TOOLS_GROQ
            payload["tool_choice"] = "auto"

        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        if not resp.ok:
            raise Exception(f"Groq API error {resp.status_code}: {resp.text}")
        return resp.json()

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        max_iterations = 10
        for i in range(max_iterations):
            try:
                data = self._call_groq(use_tools=True)
            except Exception as e:
                # Si échec avec outils, retry sans outils
                try:
                    data = self._call_groq(use_tools=False)
                except Exception as e2:
                    self.history.pop()
                    raise e2

            choice = data["choices"][0]
            message = choice["message"]
            finish_reason = choice["finish_reason"]

            self.history.append(message)

            # Réponse finale
            if finish_reason == "stop" or finish_reason is None:
                content = message.get("content") or ""
                if content:
                    return content
                # Si content vide mais tool_calls présents, on continue
                if not message.get("tool_calls"):
                    return "(pas de réponse)"

            # L'agent utilise un outil
            if finish_reason == "tool_calls" or message.get("tool_calls"):
                tool_calls = message.get("tool_calls", [])
                if not tool_calls:
                    content = message.get("content", "")
                    return content or "(pas de réponse)"

                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    try:
                        tool_args = json.loads(tc["function"]["arguments"])
                    except Exception:
                        tool_args = {}
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
                content = message.get("content", "")
                return content or "(pas de réponse)"

        return "L'agent a atteint la limite d'itérations."
