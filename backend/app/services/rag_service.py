"""AI RAG Assistant over the project's own documents.

Retrieval is real and deterministic: documents in `app/knowledge_base/*.md` (materialized from
the team's Executive Summary, finalist guidelines, presentation deck, and pitch-strategy notes)
are split into heading-level sections and indexed with TF-IDF (scikit-learn) — no network call
and no external embedding-model download required, so this works offline in any environment.

Answer synthesis has two modes:
  - "extractive" (default, always available): returns the best-matching section(s) verbatim,
    with sources. No hallucination risk — every word comes from a real project document.
  - "llm" (optional): if ANTHROPIC_API_KEY is set in the environment, the retrieved sections are
    passed as grounding context to a real Claude call, which synthesizes a natural-language
    answer instructed to only use the provided context. Falls back to "extractive" if the key is
    absent or the call fails, and always reports which mode actually produced the answer.
"""
import os
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"

SYSTEM_PROMPT = (
    "You are a farming-assistant Q&A tool. Answer the user's question using ONLY the provided "
    "context sections from the project's own documents. If the context does not contain the "
    "answer, say so plainly rather than guessing. Be concise."
)


def _split_into_sections(text: str, source: str) -> list[dict]:
    lines = text.splitlines()
    sections = []
    current_heading = "Overview"
    current_lines = []

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            sections.append({"document": source, "heading": current_heading, "text": body})

    for line in lines:
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_lines = []
        elif line.startswith("# "):
            continue
        else:
            current_lines.append(line)
    flush()
    return sections


class RAGIndex:
    def __init__(self, kb_dir: Path = KB_DIR):
        self.sections = []
        for path in sorted(kb_dir.glob("*.md")):
            text = path.read_text()
            self.sections.extend(_split_into_sections(text, path.stem))

        if not self.sections:
            raise RuntimeError(f"No knowledge base documents found in {kb_dir}")

        # Heading repeated to weight it slightly higher; bigrams help match multi-word
        # queries (e.g. "yield prediction") to the specific section over generic overviews.
        corpus = [f"{s['heading']} {s['heading']}. {s['text']}" for s in self.sections]
        self.vectorizer = TfidfVectorizer(stop_words="english", max_df=0.9, ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:top_k]:
            if scores[i] <= 0:
                continue
            s = self.sections[i]
            results.append(
                {
                    "document": s["document"],
                    "heading": s["heading"],
                    "text": s["text"],
                    "score": round(float(scores[i]), 4),
                }
            )
        return results

    def list_documents(self) -> list[str]:
        return sorted({s["document"] for s in self.sections})


_index: RAGIndex | None = None


def get_index() -> RAGIndex:
    global _index
    if _index is None:
        _index = RAGIndex()
    return _index


def _extractive_answer(sources: list[dict]) -> str:
    if not sources:
        return "No relevant content found in the project documents for this question."
    top = sources[0]
    text = re.sub(r"\s+", " ", top["text"]).strip()
    if len(text) > 700:
        text = text[:700].rsplit(" ", 1)[0] + "…"
    return f"From \"{top['document']}\" > {top['heading']}: {text}"


def _llm_answer(query: str, sources: list[dict]) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not sources:
        return None
    try:
        import anthropic

        context = "\n\n".join(
            f"[{s['document']} > {s['heading']}]\n{s['text']}" for s in sources
        )
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
        )
        return response.content[0].text
    except Exception:
        return None


def query(question: str, top_k: int = 3) -> dict:
    index = get_index()
    sources = index.search(question, top_k=top_k)

    llm_answer = _llm_answer(question, sources)
    if llm_answer:
        return {"answer": llm_answer, "mode": "llm", "sources": sources}

    return {"answer": _extractive_answer(sources), "mode": "extractive", "sources": sources}
