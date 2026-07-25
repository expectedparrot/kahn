from __future__ import annotations

import re
from importlib import resources

DOCS: dict[str, dict] = {
    "overview": {
        "title": "Package Overview",
        "summary": "What kahn does and when to use it.",
        "file": "overview.md",
    },
    "getting-started": {
        "title": "Getting Started",
        "summary": "Initialization, first commands, and typical workflow.",
        "file": "getting-started.md",
    },
    "workflow": {
        "title": "Workflow Phases",
        "summary": "The five phases of scenario planning and what to do at each.",
        "file": "workflow.md",
    },
    "best-practices": {
        "title": "Best Practices",
        "summary": "Quality standards, common pitfalls, and facilitation guidance.",
        "file": "best-practices.md",
    },
    "cli-reference": {
        "title": "CLI Quick Reference",
        "summary": "All commands with syntax, flags, and examples.",
        "file": "cli-reference.md",
    },
}


def load_doc(topic: str) -> str:
    meta = DOCS[topic]
    pkg = resources.files("kahn").joinpath("docs_content")
    return pkg.joinpath(meta["file"]).read_text(encoding="utf-8")


def search_docs(query: str) -> list[dict]:
    terms = re.findall(r"[A-Za-z0-9_-]+", query.lower())
    results = []
    for topic, meta in DOCS.items():
        text = load_doc(topic)
        haystack = f"{topic} {meta['title']} {meta['summary']} {text}".lower()
        score = sum(haystack.count(t) for t in terms)
        if score > 0:
            snippet = ""
            for term in terms:
                idx = haystack.find(term)
                if idx >= 0:
                    start = max(0, idx - 90)
                    end = min(len(text), idx + 200)
                    snippet = text[start:end].strip()
                    break
            results.append({**meta, "topic": topic, "score": score, "snippet": snippet})
    return sorted(results, key=lambda r: r["score"], reverse=True)
