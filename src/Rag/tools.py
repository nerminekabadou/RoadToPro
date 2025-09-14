# tools.py
"""
Utility tools for the multi-agent RAG system.
Provides Meta and Routine search functions using DuckDuckGo (ddgs).
"""

from ddgs import DDGS
import socket
import requests
import os
import json
import hashlib
from langchain_core.tools import tool


CACHE_DIR = "cache_tools"
os.makedirs(CACHE_DIR, exist_ok=True)


def cache_result(name, query, result=None):
    """Save or load cached results"""
    filename = os.path.join(CACHE_DIR, f"{name}_{hashlib.md5(query.encode()).hexdigest()}.json")
    if result is not None:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
    elif os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def ddgs_search(query: str, max_results: int = 5, timeout: int = 15) -> str:
    """
    Perform a DuckDuckGo text search via the ddgs library.
    Returns a formatted string of results or an error message.
    """
    print(f"[DEBUG] Starting search for: {query}")
    try:
        with DDGS(timeout=timeout) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            print(f"[DEBUG] Raw search results: {results}")
    except (socket.timeout, Exception) as e:
        return f"[Search error: {e}]"

    if not results:
        return "No results found."

    return "\n".join(f"- {r.get('title')} — {r.get('href')}" for r in results)


def get_meta(game: str) -> str:
    """
    Fetch meta information about a game (guides, strategies, etc.).
    """
    query = f"{game} meta strategy guide"
    print(f"[DEBUG] Meta query: {query}")
    result = ddgs_search(query, max_results=6)
    if result.startswith("[Search error") or result == "No results found.":
        return "⚠️ Unable to fetch meta info. Check your connection or try later."
    return f"--- Meta ---\n{result}"


def get_routines(game: str) -> str:
    """
    Fetch routine/tips for a game.
    """
    query = f"{game} routine tips tricks"
    print(f"[DEBUG] Routine query: {query}")
    result = ddgs_search(query, max_results=6)
    if result.startswith("[Search error") or result == "No results found.":
        return "⚠️ Unable to fetch routine info. Check your connection or try later."
    return f"--- Routine ---\n{result}"


@tool
def get_patch(game: str) -> str:
    """Get current patch/version for LoL, Valorant, CS2"""
    cached = cache_result("patch", game)
    if cached:
        return cached

    patch = "N/A"
    try:
        if game.lower() == "lol":
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            r = requests.get(url); r.raise_for_status()
            patch = r.json()[0]
        elif game.lower() == "valorant":
            url = "https://valorant-api.com/v1/version"
            r = requests.get(url); r.raise_for_status()
            patch = r.json().get("data", {}).get("version", "N/A")
        elif game.lower() == "cs2":
            patch = "Patch info not available for CS2."
        else:
            patch = "Unsupported game."
    except Exception as e:
        patch = f"Error fetching patch: {e}"

    cache_result("patch", game, patch)
    return patch
