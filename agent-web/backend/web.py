"""
Tool : web_search
Recherche web via DuckDuckGo (pas de clé API nécessaire).
"""

import urllib.request
import urllib.parse
import json
import re

WEB_SEARCH_SCHEMA = {
    "name": "web_search",
    "description": (
        "Effectue une recherche web et retourne les résultats pertinents. "
        "Utile pour : trouver des infos récentes, de la doc technique, "
        "des CVE/failles sécu, des tutos Linux, etc."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "La requête de recherche.",
            },
            "max_results": {
                "type": "integer",
                "description": "Nombre de résultats à retourner (défaut: 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}


def web_search_tool(query: str, max_results: int = 5) -> str:
    """Recherche via DuckDuckGo Instant Answer API."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = []

        # Réponse directe (Abstract)
        if data.get("AbstractText"):
            results.append(f"**Réponse directe :** {data['AbstractText']}")
            if data.get("AbstractURL"):
                results.append(f"Source : {data['AbstractURL']}")

        # Résultats connexes (RelatedTopics)
        topics = data.get("RelatedTopics", [])
        count = 0
        for topic in topics:
            if count >= max_results:
                break
            if isinstance(topic, dict) and topic.get("Text"):
                text = topic["Text"]
                url_topic = topic.get("FirstURL", "")
                results.append(f"\n- {text}")
                if url_topic:
                    results.append(f"  🔗 {url_topic}")
                count += 1

        if not results:
            # Fallback : retourne juste un lien de recherche Google
            google_url = f"https://www.google.com/search?q={encoded}"
            return (
                f"Pas de résultat direct depuis DuckDuckGo pour : '{query}'\n"
                f"Recherche Google : {google_url}\n\n"
                f"💡 Conseil : installe `googlesearch-python` pour de meilleurs résultats web."
            )

        return "\n".join(results)

    except Exception as e:
        return f"Erreur recherche web : {str(e)}"
