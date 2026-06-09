"""
Tools : read_file / write_file
Lecture et écriture de fichiers locaux.
"""

import os

READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": (
        "Lit le contenu d'un fichier local. "
        "Utile pour analyser des configs (sshd_config, nginx.conf), "
        "du code source, des logs, des fichiers texte, CSV, JSON, etc."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Chemin absolu ou relatif vers le fichier à lire.",
            },
            "max_lines": {
                "type": "integer",
                "description": "Nombre max de lignes à lire (défaut: 200). Utile pour les gros fichiers.",
                "default": 200,
            },
        },
        "required": ["path"],
    },
}

WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": (
        "Écrit ou écrase un fichier local avec le contenu fourni. "
        "Utile pour créer des scripts, sauvegarder des configs, écrire des notes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Chemin absolu ou relatif vers le fichier à écrire.",
            },
            "content": {
                "type": "string",
                "description": "Contenu à écrire dans le fichier.",
            },
        },
        "required": ["path", "content"],
    },
}


def read_file_tool(path: str, max_lines: int = 200) -> str:
    try:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Fichier introuvable : {path}"
        if not os.path.isfile(path):
            return f"❌ Ce n'est pas un fichier : {path}"

        size = os.path.getsize(path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total = len(lines)
        truncated = total > max_lines
        content = "".join(lines[:max_lines])

        header = f"📄 {path} ({total} lignes, {size} octets)"
        if truncated:
            header += f" — tronqué aux {max_lines} premières lignes"

        return f"{header}\n\n{content}"
    except Exception as e:
        return f"Erreur lecture : {str(e)}"


def write_file_tool(path: str, content: str) -> str:
    try:
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Fichier écrit : {path} ({len(content)} caractères)"
    except Exception as e:
        return f"Erreur écriture : {str(e)}"
