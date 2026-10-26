#!/usr/bin/env python3
"""Build a tabular candidate list and stable citation keys from archived selection metadata."""
from __future__ import annotations
import csv, json, re, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/bibliometria/candidatos.json"
OUT = ROOT / "data/bibliometria/candidatos.csv"
STOP = {"de", "da", "das", "do", "dos", "e", "van", "von", "del", "della"}

def ascii_slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9]+", "", text)

def first_family(authors: str) -> str:
    first = authors.split(",", 1)[0].strip()
    parts = [x for x in re.split(r"\s+", first) if x]
    for part in reversed(parts):
        if part.lower() not in STOP:
            return ascii_slug(part) or "Author"
    return ascii_slug(parts[-1]) if parts else "Author"

def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    records = data["records"]
    if len(records) != 80:
        raise SystemExit(f"Esperados 80 registros; encontrados {len(records)}")
    used = set()
    out = []
    for r in records:
        year = int(r["year"])
        slug = re.findall(r"[A-Za-z0-9]+", unicodedata.normalize("NFKD", r["title"]).encode("ascii", "ignore").decode("ascii"))
        title_token = (slug[0] if slug else "article")[:8].lower()
        base = f"{first_family(r['authors'])}{year}{title_token}"
        key, n = base, 2
        while key.lower() in used:
            key = f"{base}{n}"; n += 1
        used.add(key.lower())
        out.append({
            "id": r["id"], "doi": r["doi"], "doi_canonical": r["doi"].strip().lower(),
            "citation_key": key, "title": r["title"], "authors": r["authors"],
            "journal": r["journal"], "year": year,
            "publisher_or_index_url": r.get("publisher_or_index_url", ""),
            "topic": r.get("topic", ""), "peer_reviewed": "pending_source_check",
            "document_type": "journal-article (candidate; verify)",
            "metadata_source": "Crossref DOI record (candidate; verify)",
            "verified_source": "pending"
        })
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    print(f"Wrote {len(out)} candidates; distinct DOIs={len({x['doi_canonical'] for x in out})}; CSV={OUT}")

if __name__ == "__main__":
    main()
