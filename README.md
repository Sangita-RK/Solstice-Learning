# Starter Kit — Docs Q&A Assistant

## Contents

- `data/docs.json` — 6 synthetic documentation articles covering common product topics.
- `data/example_questions.json` — 5 example questions to test against, including one that isn't covered by any doc.
- `main.py` — an interactive keyword-based assistant that returns a matching source passage, abstains on weak matches, and asks for clarification when multiple topics score similarly.
- `tests/test_main.py` — tests for the provided examples, a paraphrase, an unsupported question, and an ambiguous question.
- `docs_qa_utils.py` — a small Python utility module with text normalization and keyword-matching helpers.

## A few notes

- Run the assistant from this folder with `python main.py`.
- Run the tests with `python -m unittest discover -s tests`.
- Retrieval weights rarer query terms more heavily. A direct answer requires at least two matched terms and `0.6` weighted query coverage; close matches across different documents trigger a clarification prompt even when the question is short. These are conservative keyword heuristics, not calibrated confidence probabilities.
- The assistant shows a source sentence rather than generating a new answer. A matching passage is evidence, but keyword overlap alone cannot guarantee that it fully answers the question.
- When evidence is weak, the assistant abstains and suggests adding the feature, action, or plan to the question. Ambiguous matches list the candidate topics and ask the user to choose.
- Not every question in `data/example_questions.json` is covered by the docs. The tests check that the Salesforce question is rejected rather than guessed.
