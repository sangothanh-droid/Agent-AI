"""
Tool : bash
Exécute des commandes shell sur la machine locale.
Windows : PowerShell | Linux/Mac : bash
"""

import subprocess
import sys

BASH_SCHEMA = {
    "name": "bash",
    "description": (
        "Exécute une commande shell sur la machine locale. "
        "Sur Windows : PowerShell. Sur Linux/Mac : bash. "
        "Utile pour : lister des fichiers, voir des logs, tester des configs réseau, "
        "lancer des scripts Python, vérifier des services, etc. "
        "Retourne stdout + stderr + le code de retour."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "La commande à exécuter (PowerShell sur Windows, bash sur Linux).",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout en secondes (défaut: 30).",
                "default": 30,
            },
        },
        "required": ["command"],
    },
}


def bash_tool(command: str, timeout: int = 30) -> str:
    try:
        if sys.platform == "win32":
            # PowerShell sur Windows
            args = ["powershell", "-NoProfile", "-Command", command]
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            # bash sur Linux/Mac
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}"
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        output += f"\nCode de retour: {result.returncode}"
        return output.strip() or "(aucune sortie)"
    except subprocess.TimeoutExpired:
        return f"⏱️ Timeout après {timeout}s"
    except Exception as e:
        return f"Erreur: {str(e)}"
