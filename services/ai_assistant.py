"""Evidence-grounded local LLM service for Phase 5.

Uses Ollama's local HTTP API. The LLM receives retrieved project evidence,
not the full evidence store. Source records are maintained by the application.
"""
from __future__ import annotations

import os
from typing import Any

import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:31b")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "90"))

SYSTEM_PROMPT = """You are an AI assistant for digital evidence analysis.

Use ONLY the evidence context supplied by the application.
Never invent facts, entities, relationships, dates, transactions, locations,
identities, or events. Do not use outside knowledge to fill missing evidence.
If the context is insufficient, say: "The available evidence does not contain
enough information to answer this question."
Do not declare anyone guilty or innocent and do not make unsupported accusations.
Clearly distinguish evidence from interpretation. Mention Evidence IDs and
record/page information when available. If evidence conflicts, state that it
conflicts. Be concise and factual.
"""


def ollama_status() -> tuple[bool, str]:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        names = [m.get("name", "") for m in models]
        if OLLAMA_MODEL not in names:
            return True, f"Ollama is running, but model '{OLLAMA_MODEL}' is not downloaded."
        return True, f"Connected to Ollama. Model: {OLLAMA_MODEL}"
    except requests.RequestException:
        return False, "Ollama is not running or cannot be reached."
    except (ValueError, TypeError):
        return False, "Ollama returned an unexpected response."


def _format_context(context: dict[str, Any]) -> str:
    lines = ["EVIDENCE CONTEXT", ""]
    for e in context.get("evidence", []):
        lines.append(f"Evidence ID: {e.get('evidence_id')}")
        lines.append(f"Source: {e.get('original_filename')}")
        lines.append(f"File type: {e.get('file_type')}")
        lines.append("")

    if context.get("entities"):
        lines.append("ENTITIES")
        for e in context["entities"]:
            loc = e.get("record_number") or e.get("page_number") or "-"
            lines.append(
                f"- {e.get('entity_text')} [{e.get('entity_type')}] | "
                f"Evidence {e.get('evidence_id')} | Record/Page {loc} | "
                f"Source {e.get('source_filename')}"
            )

    if context.get("relationships"):
        lines.append("")
        lines.append("RELATIONSHIPS")
        for r in context["relationships"]:
            loc = r.get("record_number") or r.get("page_number") or "-"
            lines.append(
                f"- {r.get('source_entity_text')} [{r.get('source_entity_type')}] "
                f"--{r.get('relationship_type')}--> {r.get('target_entity_text')} "
                f"[{r.get('target_entity_type')}] | Evidence {r.get('evidence_id')} | "
                f"Record/Page {loc} | Source {r.get('source_filename')}"
            )
    return "\n".join(lines)


def build_prompt(question: str, context: dict[str, Any]) -> str:
    return f"{_format_context(context)}\n\nUSER QUESTION:\n{question}\n\nAnswer using only the evidence context above."


def ask_ollama(question: str, context: dict[str, Any]) -> str:
    if not context.get("has_results"):
        return "No relevant evidence was found for this question."

    payload = {
        "model": OLLAMA_MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": build_prompt(question, context),
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        headers = {
    "Authorization": f"Bearer {OLLAMA_API_KEY}",
    "Content-Type": "application/json",
}

response = requests.post(
    f"{OLLAMA_BASE_URL}/api/generate",
    headers=headers,
    json=payload,
    timeout=OLLAMA_TIMEOUT,
)
        response.raise_for_status()
        data = response.json()
        answer = str(data.get("response", "")).strip()
        if not answer:
            return "The local AI model returned an empty response."
        return answer
    except requests.RequestException as exc:
        return f"Ollama could not be reached. Start Ollama and try again. ({exc.__class__.__name__})"
    except (ValueError, TypeError):
        return "Ollama returned an invalid response."


def answer_question(question: str, context: dict[str, Any]) -> str:
    return ask_ollama(question.strip(), context)
