"""
gutenberg_novels.py
Search and download public-domain novels from Project Gutenberg via Gutendex.

Usage examples:
  # 1) Top 5 English novels related to "kyoto"
  python gutenberg_novels.py --query "kyoto" --lang en --limit 5 --out ./books

  # 2) A few classic authors
  python gutenberg_novels.py --author "jules verne" --limit 3

  # 3) Random popular English novels
  python gutenberg_novels.py --random --limit 5
"""

from __future__ import annotations
import argparse
import json
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
GUTENDEX = "https://gutendex.com/books"

# --- Helpers -----------------------------------------------------------------

def _pick_best_download(formats: Dict[str, str]) -> Optional[Tuple[str, str]]:
    """
    Prefer DRM-free, offline-friendly formats:
      1) application/epub+zip (no images) or (images) if available
      2) text/plain; charset=utf-8
    Avoid HTML (needs online assets) and zip of text if possible.
    Returns (mime, url) or None.
    """
    # Some entries have separate "epub.images" and "epub.noimages" URLs
    epub_candidates = [k for k in formats.keys() if k.startswith("application/epub+zip")]
    # Prefer noimages if bandwidth is tight; otherwise any epub
    for key in sorted(epub_candidates, key=lambda k: (".noimages" not in k, k)):
        url = formats.get(key)
        if url:# and not url.endswith(".images"):  # many are just .epub
            return (key, url)
    # Plain text UTF-8 is nice for readers that reflow text
    for key in ["text/plain; charset=utf-8", "text/plain"]:
        url = formats.get(key)
        if url and url.endswith(".txt"):# and "zip" not in url:
           return (key, url)
    # Fallback: a zip containing text
    for key, url in formats.items():
        if "text/plain" in key and url.endswith(".zip"):
            return (key, url)
    return None

def _pick_cover(formats: Dict[str, str]) -> Optional[str]:
    # Gutendex exposes covers as "image/jpeg" or "image/png"
    for k in ["image/jpeg", "image/png"]:
        if k in formats and formats[k].lower().startswith("http"):
            return formats[k]
    return None

def _safe_name(s: str) -> str:
    keep = "".join(c for c in s if c.isalnum() or c in (" ", "_", "-", "."))
    return "_".join(keep.split())[:120] or "book"

def _get(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    r = requests.get(url, params=params, timeout=30, headers={"User-Agent": "GutenHack/1.0 (+noncommercial demo)"})
    r.raise_for_status()
    return r.json()

def _download_file(url: str, out_path: Path) -> None:
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "GutenHack/1.0"}) as r:
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)

# --- Search ------------------------------------------------------------------

def search_gutenberg(
    query: Optional[str],
    author: Optional[str],
    lang: str,
    limit: int,
    require_novel: bool,
    randomize: bool,
) -> List[Dict[str, Any]]:
    """
    Queries Gutendex and returns up to `limit` book objects.
    We bias toward 'novel' subjects and English (configurable).
    """
    params = {
        "languages": lang if lang else "en",
        "mime_type": None,               # let us pick formats ourselves
        "topic": None,                   # we’ll filter subjects locally if needed
        "search": None,
        "author_year_start": None,
        "author_year_end": None,
    }

    # Build Gutendex search string: it matches titles/authors/subjects
    terms = []
    if query:
        terms.append(query)
    if author:
        terms.append(f'author:"{author}"')
    if require_novel:
        terms.append("novel")
    if terms:
        params["search"] = " ".join(terms)

    results: List[Dict[str, Any]] = []
    url = GUTENDEX
    while len(results) < limit and url:
        payload = _get(url, {k: v for k, v in params.items() if v})
        page_books = payload.get("results", [])
        results.extend(page_books)
        url = payload.get("next")

    # Optional local subject filter to enforce “novel”
    if require_novel:
        results = [b for b in results if any("novel" in s.lower() for s in b.get("subjects", []))] or results

    # Randomize if requested, else rely on Gutendex default (often popularity)
    if randomize:
        random.shuffle(results)

    return results[:limit]

# --- Download ----------------------------------------------------------------

def download_books(books: List[Dict[str, Any]], out_dir: Path, pause_sec: float = 0.5) -> List[Dict[str, Any]]:
    """
    For each book, pick a good format, download it (and cover), and write metadata.json.
    Returns a list with local file info added.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    enriched: List[Dict[str, Any]] = []

    for b in books:
        book_id = b.get("id")
        title = b.get("title") or f"Gutenberg {book_id}"
        author_names = ", ".join(a.get("name", "") for a in b.get("authors", [])) or "Unknown"
        formats: Dict[str, str] = b.get("formats", {}) or {}
        chosen = _pick_best_download(formats)
        cover_url = _pick_cover(formats)

        safe = _safe_name(f"{title} - {author_names}")
        book_dir = out_dir / safe
        book_dir.mkdir(parents=True, exist_ok=True)

        local_book = None
        if chosen:
            mime, url = chosen
            ext = ".epub" if "epub" in mime else ".txt" if "text/plain" in mime else ".bin"
            local_book = book_dir / f"book{ext}"
            try:
                _download_file(url, local_book)
            except Exception as e:
                print(f"[warn] failed to download book {book_id}: {e}")
                local_book = None
        else:
            print(f"[skip] no suitable format for {title}")

        local_cover = None
        if cover_url:
            try:
                ext = ".jpg" if cover_url.endswith(".jpg") else ".png"
                local_cover = book_dir / f"cover{ext}"
                _download_file(cover_url, local_cover)
            except Exception:
                local_cover = None

        meta = {
            "id": book_id,
            "title": title,
            "authors": [a.get("name") for a in b.get("authors", [])],
            "languages": b.get("languages"),
            "subjects": b.get("subjects"),
            # store full path so later readers can open the file
            "downloaded_file": str(local_book) if local_book else None,
            "cover_file": str(local_cover) if local_cover else None,
            "gutenberg_url": f"https://www.gutenberg.org/ebooks/{book_id}",
            "license": "Public Domain (check your jurisdiction)",
            "word_count_hint": b.get("download_count"),  # Gutendex does not expose word counts; keeping downloads metric
        }
        with open(book_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        enriched.append(meta)
        time.sleep(pause_sec)  # be polite

    return enriched

# --- CLI ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Download public-domain novels from Project Gutenberg (via Gutendex)")
    ap.add_argument("--query", type=str, default=None, help="search text (title/subject/keywords)")
    ap.add_argument("--author", type=str, default=None, help="author filter (e.g., 'jules verne')")
    ap.add_argument("--lang", type=str, default="en", help="language code (default: en)")
    ap.add_argument("--limit", type=int, default=5, help="number of books to fetch")
    ap.add_argument("--out", type=Path, default=Path.home() / "gutenberg_books", help="output directory")
    ap.add_argument("--random", action="store_true", help="shuffle results (nice for variety)")
    ap.add_argument("--strict-novel", action="store_true", help="enforce 'novel' subject")
    args = ap.parse_args()

    # ensure output dir is writable (try to create and write a temp file)
    out_dir = args.out
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        test_file = out_dir / ".write_test"
        with open(test_file, "w") as tf:
            tf.write("ok")
        test_file.unlink()
    except Exception as e:
        ap.error(f"output directory {out_dir!s} is not writable: {e}")

    books = search_gutenberg(
         query=args.query,
         author=args.author,
         lang=args.lang,
         limit=args.limit,
         require_novel=args.strict_novel,
         randomize=args.random,
     )
    print(f"Found {len(books)} books; downloading to {args.out}…")
    metas = download_books(books, args.out)

    index_path = args.out / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)
    print(f"Done. Wrote {index_path}")
    for i in metas:
       epub_file = i.get("downloaded_file")
       text = get_epub_text(epub_file)
       print(text[:10000])


<<<<<<< HEAD
=======


>>>>>>> db090b3 (Rename project)
def get_epub_text(epub_path):
    if not epub_path:
        return ""
    p = Path(epub_path)
    if not p.exists():
        return ""
    # plain text files
    if p.suffix.lower() == ".txt":
        try:
            return p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    # epub files
    try:
        book = epub.read_epub(str(p))
    except Exception:
        return ""
    text_content = []
    for item in book.get_items():
        try:
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text_content.append(soup.get_text())
        except Exception:
            continue
    return "\n".join(text_content)

<<<<<<< HEAD
# --- NEW FUNCTION FOR UI ---

def get_all_downloaded_books_text() -> str:
    """
    Scans the default download directory for index.json,
    reads all downloaded books (epub or txt), and returns
    their combined text.
    """
    # This path is based on the default in your main() function
    default_dir = Path.home() / "gutenberg_books"
    index_path = default_dir / "index.json"

    if not index_path.exists():
        return (f"Error: index.json not found.\n\n"
                f"Please run this script from your terminal first to download books:\n"
                f"python {__file__} --query \"some query\"")

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            metas = json.load(f)
    except Exception as e:
        return f"Error reading {index_path}: {e}"

    if not metas:
        return "No books found in index.json. Please run the download script."

    all_books_text = []
    for i, meta in enumerate(metas):
        title = meta.get("title", "Unknown Title")
        # Ensure authors is a list before joining
        authors_list = meta.get("authors", ["Unknown Author"])
        if not isinstance(authors_list, list):
            authors_list = ["Unknown Author"]
        authors = ", ".join(authors_list)
        
        epub_file = meta.get("downloaded_file")

        header = f"--- BOOK {i+1}: {title} by {authors} ---\n\n"
        all_books_text.append(header)

        if not epub_file:
            text = "[Book file not found in metadata]\n\n"
        else:
            text = get_epub_text(epub_file)
            if not text:
                text = f"[Could not read or parse book file: {epub_file}]\n\n"
        
        all_books_text.append(text)
        all_books_text.append("\n" + ("=" * 80) + "\n\n")

    return "".join(all_books_text)

# --- END OF NEW FUNCTION ---
if __name__ == "__main__":
    main()
