# Starter Kit — Docs Q&A Assistant

## Contents

- `data/docs/` — documentation articles stored as individual files. The loader supports Markdown, text, JSON, PDF, and Word `.docx` files and searches nested folders.
- `data/example_questions.json` — 5 example questions to test against, including one that isn't covered by any doc.
- `main.py` — an interactive keyword-based assistant that returns a matching source passage, abstains on weak matches, and asks for clarification when multiple topics score similarly.
- `tests/test_main.py` — tests for the provided examples, a paraphrase, an unsupported question, and an ambiguous question.
- `docs_qa_utils.py` — document loading, text normalization, and keyword-matching helpers.

## A few notes

- Run the assistant from this folder with `python main.py`.
- Run the tests with `python -m unittest discover -s tests`.
- Install file-format support with `python -m pip install -r requirements.txt`.
- Add documentation as `.md`, `.txt`, `.json`, `.pdf`, or `.docx` files under `data/docs/` (subfolders are scanned too). Markdown files use the first `#` heading as the title; PDF metadata and Word document title metadata are used when available. Use filenames such as `D-07-password-help.pdf` to keep a stable source ID.
- Try the sample PDF `data/docs/D-07-course-access.pdf` with: “How long does course access last after enrollment?” The expected answer is 12 months.
- PDF support extracts selectable text only. Scanned/image-only PDFs need OCR before they can be searched; the loader reports those files instead of silently ignoring them.
- Retrieval weights rarer query terms more heavily. A direct answer requires at least two matched terms and `0.6` weighted query coverage; close matches across different documents trigger a clarification prompt even when the question is short. These are conservative keyword heuristics, not calibrated confidence probabilities.
- Password-change phrasings such as "change my password", "changing password", and "update my password" are normalized to the documented password-reset topic. Retrieval checks single sentences and adjacent two-sentence passages; it does not provide general-purpose semantic synonym matching.
- The assistant shows a source sentence rather than generating a new answer. A matching passage is evidence, but keyword overlap alone cannot guarantee that it fully answers the question.
- When evidence is weak, the assistant abstains rather than guessing. Ambiguous matches list the candidate topics and ask the user to choose; vague single-topic questions ask for more detail.
- Not every question in `data/example_questions.json` is covered by the docs. The tests check that the Salesforce question is rejected rather than guessed.
