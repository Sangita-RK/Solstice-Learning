"""
Small utility module provided as an optional starting point for the
docs Q&A assistant case study.

Feel free to use, modify, replace, or ignore this entirely -- it is not
guaranteed to be complete or bug-free.
"""
import json
import re
from pathlib import Path

CHUNK_SIZE = 400


def load_docs(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("docs", [])


def _load_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise ImportError(
            "Reading PDF documentation requires pypdf. "
            "Install project dependencies with 'python -m pip install -r requirements.txt'."
        ) from error

    reader = PdfReader(path)
    content = "\n".join(
        text.strip()
        for page in reader.pages
        if (text := page.extract_text())
        and text.strip()
    ).strip()
    if not content:
        raise ValueError(
            f"No selectable text found in PDF {path}; scanned PDFs need OCR "
            "before they can be searched."
        )

    title = Path(path).stem.replace("-", " ").replace("_", " ").title()
    if reader.metadata and reader.metadata.title:
        title = reader.metadata.title.strip() or title
    return title, content


def _load_docx(path):
    try:
        from docx import Document
    except ImportError as error:
        raise ImportError(
            "Reading Word documentation requires python-docx. "
            "Install project dependencies with 'python -m pip install -r requirements.txt'."
        ) from error

    document = Document(path)
    parts = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))

    content = "\n".join(parts)
    if not content:
        raise ValueError(f"No text found in Word document {path}")

    title = document.core_properties.title.strip() or (
        Path(path).stem.replace("-", " ").replace("_", " ").title()
    )
    return title, content


def load_docs_from_folder(folder):
    """Load documentation records from supported files in a folder tree."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Documentation folder does not exist: {folder}")

    docs = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()
        if suffix == ".json":
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict) and isinstance(data.get("docs"), list):
                records = data["docs"]
            elif isinstance(data, dict) and all(
                key in data for key in ("doc_id", "title", "content")
            ):
                records = [data]
            else:
                raise ValueError(
                    f"Expected a document or a 'docs' list in {path}"
                )
            for record in records:
                if (
                    not isinstance(record, dict)
                    or not all(
                        isinstance(record.get(key), str) and record[key].strip()
                        for key in ("doc_id", "title", "content")
                    )
                ):
                    raise ValueError(
                        f"Each document in {path} needs doc_id, title, and content"
                    )
                docs.append(record)
        elif suffix in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue

            title = path.stem.replace("-", " ").replace("_", " ").title()
            content = text
            heading = re.match(r"^#\s+(.+?)\s*(?:\r?\n|$)", text)
            if heading:
                title = heading.group(1)
                content = text[heading.end():].strip()
                title_id = re.match(r"^(D-\d+)\s*[:|—-]\s*(.+)$", title)
                if title_id:
                    title = title_id.group(2).strip()

            id_match = re.match(r"^(D-\d+)(?:[-_]|$)", path.stem, re.IGNORECASE)
            doc_id = id_match.group(1).upper() if id_match else path.stem
            docs.append({
                "doc_id": doc_id,
                "title": title,
                "content": content,
            })
        elif suffix == ".pdf":
            title, content = _load_pdf(path)
            id_match = re.match(r"^(D-\d+)(?:[-_]|$)", path.stem, re.IGNORECASE)
            doc_id = id_match.group(1).upper() if id_match else path.stem
            docs.append({
                "doc_id": doc_id,
                "title": title,
                "content": content,
            })
        elif suffix == ".docx":
            title, content = _load_docx(path)
            id_match = re.match(r"^(D-\d+)(?:[-_]|$)", path.stem, re.IGNORECASE)
            doc_id = id_match.group(1).upper() if id_match else path.stem
            docs.append({
                "doc_id": doc_id,
                "title": title,
                "content": content,
            })

    if not docs:
        raise ValueError(f"No supported documentation files found in {folder}")

    ids = [doc["doc_id"] for doc in docs]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate document IDs found in {folder}")
    return docs


def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Split text into fixed-size chunks."""
    chunks = []
    num_chunks = len(text) // chunk_size
    for i in range(num_chunks):
        start = i * chunk_size
        chunks.append(text[start:start + chunk_size])
    return chunks


def chunk_all_docs(docs, chunk_size=CHUNK_SIZE):
    """Return a flat list of {doc_id, title, chunk_index, text} dicts."""
    all_chunks = []
    for doc in docs:
        for idx, chunk in enumerate(chunk_text(doc["content"], chunk_size)):
            all_chunks.append({
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "chunk_index": idx,
                "text": chunk,
            })
    return all_chunks


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [tok for tok in text.split() if tok]


def keyword_overlap_score(query_tokens, chunk_tokens):
    shared = set(query_tokens) & set(chunk_tokens)
    if not chunk_tokens:
        return 0.0
    return len(shared) / len(set(query_tokens) | set(chunk_tokens))


def find_best_chunks(question, chunks, top_n=3):
    q_tokens = normalize_text(question)
    scored = []
    for chunk in chunks:
        score = keyword_overlap_score(q_tokens, normalize_text(chunk["text"]))
        scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:top_n]
