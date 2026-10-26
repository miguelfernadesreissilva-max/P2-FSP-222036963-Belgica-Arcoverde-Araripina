#!/usr/bin/env python3
"""Compare the seed bibliography candidates with Crossref registration metadata.
Publisher/peer-review verification remains a separate field supplied by source checks.
"""
from __future__ import annotations
import csv
import difflib
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/bibliometria/candidatos.json"
OUT_JSON = ROOT / "data/bibliometria/crossref_verification.json"
OUT_CSV = ROOT / "data/bibliometria/crossref_verification.csv"
USER_AGENT = "P2-FSP-222036963/1.0 (academic bibliographic metadata validation)"


def norm(text: str | None) -> str:
    text = text or ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def year_from(message: dict) -> int | None:
    for key in ("published-print", "published", "issued", "published-online"):
        date = message.get(key, {}).get("date-parts", [])
        if date and date[0]:
            try:
                return int(date[0][0])
            except (TypeError, ValueError):
                pass
    return None


def crossref_record(record: dict) -> dict:
    doi = record["doi"].strip()
    url = "https://api.crossref.org/works/" + quote(doi, safe="")
    last = None
    for attempt in range(4):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=(15, 60))
            if r.status_code == 429 or r.status_code >= 500:
                last = f"HTTP {r.status_code}"
                time.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code != 200:
                return {"id": record["id"], "doi": doi, "http_status": r.status_code, "error": r.text[:300]}
            msg = r.json().get("message", {})
            title = (msg.get("title") or [""])[0]
            journal = (msg.get("container-title") or [""])[0]
            authors = "; ".join(" ".join(x for x in [a.get("given"), a.get("family")] if x) for a in msg.get("author", []))
            year = year_from(msg)
            title_sim = difflib.SequenceMatcher(None, norm(record.get("title")), norm(title)).ratio()
            journal_sim = difflib.SequenceMatcher(None, norm(record.get("journal")), norm(journal)).ratio()
            cand_year = int(record["year"]) if record.get("year") else None
            year_ok = year is not None and cand_year is not None and abs(year - cand_year) <= 1
            type_ok = msg.get("type") == "journal-article"
            # Similarity is a screening flag; all mismatches are retained for manual/source review.
            match = bool(type_ok and title_sim >= 0.85 and journal_sim >= 0.70 and year_ok)
            return {
                "id": record["id"], "doi": doi, "doi_crossref": msg.get("DOI", ""),
                "crossref_type": msg.get("type", ""), "title_crossref": title,
                "authors_crossref": authors, "journal_crossref": journal, "year_crossref": year,
                "publisher_crossref": msg.get("publisher", ""), "title_similarity": round(title_sim, 4),
                "journal_similarity": round(journal_sim, 4), "year_within_one": year_ok,
                "type_journal_article": type_ok, "metadata_match_screen": match,
                "crossref_url": url, "publisher_landing_url": msg.get("URL", ""),
                "license": "; ".join(x.get("URL", "") for x in msg.get("license", [])),
                "error": ""
            }
        except Exception as exc:  # Preserve errors for transparent manual review.
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(1.0 * (attempt + 1))
    return {"id": record["id"], "doi": doi, "http_status": "failed", "error": last or "unknown"}


def main() -> None:
    records = json.loads(SOURCE.read_text(encoding="utf-8"))["records"]
    if len(records) != 80:
        raise SystemExit(f"Esperados 80 candidatos; recebidos {len(records)}")
    results = [None] * len(records)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(crossref_record, rec): i for i, rec in enumerate(records)}
        for fut in as_completed(futures):
            results[futures[fut]] = fut.result()
    result_by_id = {str(r.get("id")): r for r in results}
    merged = []
    for rec in records:
        cross = result_by_id.get(str(rec["id"]), {})
        merged.append({**rec, **cross})
    OUT_JSON.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = sorted({k for row in merged for k in row})
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)
    passed = sum(bool(r.get("metadata_match_screen")) for r in merged)
    errors = sum(bool(r.get("error")) for r in merged)
    print(f"Crossref responses: {len(merged)}; screening match: {passed}; errors requiring follow-up: {errors}")
    print(f"JSON: {OUT_JSON}\nCSV: {OUT_CSV}")


if __name__ == "__main__":
    main()
