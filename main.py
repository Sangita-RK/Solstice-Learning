import re
from dataclasses import dataclass
from math import log
from pathlib import Path
from typing import Literal

from docs_qa_utils import load_docs, normalize_text


MINIMUM_SCORE = 0.6
MINIMUM_MATCHED_TERMS = 2
AMBIGUITY_MARGIN = 0.15
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "before", "but",
    "by", "can", "could", "do", "does", "for", "from", "has", "have",
    "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or",
    "our", "the", "their", "then", "this", "to", "us", "was", "we",
    "what", "when", "where", "which", "who", "why", "will", "with",
    "number",
    "would", "you", "your",
}


@dataclass
class SearchResult:
    status: Literal["answer", "abstain", "ambiguous"]
    doc_id: str | None = None
    title: str | None = None
    passage: str | None = None
    score: float = 0.0
    alternatives: tuple[str, ...] = ()
    message: str | None = None
    matched_terms: int = 0


def _meaningful_tokens(text):
    tokens = set()
    for token in normalize_text(text):
        if token in STOP_WORDS:
            continue
        if token in {"maximum", "max", "capped"}:
            token = "cap"
        elif token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("s") and not token.endswith("ss") and len(token) > 3:
            token = token[:-1]
        tokens.add(token)
    return tokens


def _passages(docs):
    for doc in docs:
        for passage in re.split(r"(?<=[.!?])\s+", doc["content"].strip()):
            if passage:
                yield doc, passage


def answer_question(question, docs):
    query_tokens = _meaningful_tokens(question)
    if not query_tokens:
        return SearchResult(
            "abstain",
            message="Please ask a question about a specific product task or policy.",
        )

    document_tokens = {
        doc["doc_id"]: _meaningful_tokens(doc["content"])
        for doc in docs
    }
    document_frequency = {
        token: sum(token in tokens for tokens in document_tokens.values())
        for token in query_tokens
    }
    query_weights = {
        token: log((len(document_tokens) + 1) / (document_frequency[token] + 1)) + 1
        for token in query_tokens
    }
    total_query_weight = sum(query_weights.values())

    best_by_doc = {}
    for doc, passage in _passages(docs):
        passage_tokens = _meaningful_tokens(passage)
        matched_tokens = query_tokens & passage_tokens
        score = (
            sum(query_weights[token] for token in matched_tokens)
            / total_query_weight
        )
        current = best_by_doc.get(doc["doc_id"])
        if current is None or score > current.score:
            best_by_doc[doc["doc_id"]] = SearchResult(
                status="answer",
                doc_id=doc["doc_id"],
                title=doc["title"],
                passage=passage,
                score=score,
                matched_terms=len(matched_tokens),
            )

    ranked = sorted(best_by_doc.values(), key=lambda result: result.score, reverse=True)
    if not ranked or ranked[0].score < MINIMUM_SCORE:
        return SearchResult(
            "abstain",
            message=(
                "I couldn't find enough matching documentation to answer reliably. "
                "Try including the feature, action, or plan you're asking about."
            ),
        )

    plausible = [
        result
        for result in ranked
        if result.score >= MINIMUM_SCORE
        and ranked[0].score - result.score <= AMBIGUITY_MARGIN
    ]
    if len(plausible) > 1:
        return SearchResult(
            status="ambiguous",
            alternatives=tuple(result.title for result in plausible),
        )

    if ranked[0].matched_terms < MINIMUM_MATCHED_TERMS:
        return SearchResult(
            "abstain",
            message=(
                "I need a little more detail to find a reliable answer. "
                "Please include the feature, action, or plan you're asking about."
            ),
        )

    return ranked[0]


def main():
    docs_path = Path(__file__).parent / "data" / "docs.json"
    docs = load_docs(docs_path)

    print("Docs Q&A Assistant (type 'quit' to exit)")
    while True:
        question = input("\nAsk a question: ").strip()
        if question.lower() == "quit":
            break

        result = answer_question(question, docs)
        if result.status == "answer":
            print("\nAnswer (from the documentation):")
            print(result.passage)
            print(f"Source: {result.title} ({result.doc_id})")
        elif result.status == "ambiguous":
            topics = ", ".join(result.alternatives)
            print(
                f"I found documentation for multiple topics: {topics}. "
                "Which topic should I focus on?"
            )
        else:
            print(
                result.message
                or "I don't have an answer for that in the documentation."
            )


if __name__ == "__main__":
    main()
