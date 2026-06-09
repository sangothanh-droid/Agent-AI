"""
Tool : get_datetime
Retourne la date et l'heure actuelles.
"""

from datetime import datetime

DATETIME_SCHEMA = {
    "name": "get_datetime",
    "description": "Retourne la date et l'heure actuelles sur la machine locale.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def datetime_tool() -> str:
    now = datetime.now()
    return now.strftime("📅 %A %d %B %Y — %H:%M:%S")
