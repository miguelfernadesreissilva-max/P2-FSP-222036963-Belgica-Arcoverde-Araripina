#!/usr/bin/env python3
"""Coleta dados oficiais brutos para a P2; preserva as respostas originais em JSON."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "brutos"
SICONFI = "https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/dca"
SIDRA = "https://apisidra.ibge.gov.br/values"

SIDRA_QUERIES = {
    "ibge_pop_estimativas_2015_2024.json": f"{SIDRA}/t/6579/n6/2601201,2601102/v/9324/p/2015-2024",
    "ibge_censo2022_populacao.json": f"{SIDRA}/t/4709/n6/2601201,2601102/v/93/p/2022",
    "ibge_pib_municipal_2015_2023.json": f"{SIDRA}/t/5938/n6/2601201,2601102/v/37/p/2015-2023",
    "ibge_ipca_mensal_2015_2024.json": f"{SIDRA}/t/1737/n1/1/v/2266/p/201501-202412",
}
EUROSTAT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "gov_10dd_edpt1?geo=BE"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_siconfi_files(refresh: bool = False) -> list[dict]:
    """Download missing annual DCA files. Use --refresh to replace existing files."""
    manifest = []
    session = requests.Session()
    session.headers.update({"User-Agent": "P2-FSP-222036963-data-reproduction/1.0"})
    for code, city in [(2601201, "arcoverde"), (2601102, "araripina")]:
        for year in range(2015, 2025):
            name = f"siconfi_dca_{city}_{year}.json"
            path = RAW / name
            url = f"{SICONFI}?an_exercicio={year}&id_ente={code}"
            if refresh or not path.exists():
                last_error = None
                for attempt in range(5):
                    try:
                        response = session.get(url, timeout=90)
                        response.raise_for_status()
                        payload = response.json()
                        if "items" not in payload or "hasMore" not in payload:
                            raise ValueError(f"Resposta Siconfi com esquema inesperado: {name}")
                        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        last_error = None
                        break
                    except Exception as exc:  # mantém erro e limita tentativas
                        last_error = exc
                        time.sleep(min(2 ** attempt, 16))
                if last_error:
                    raise RuntimeError(f"Falha ao coletar {url}: {last_error}")
                time.sleep(1.05)  # limite recomendado pelo Siconfi
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("hasMore"):
                raise RuntimeError(f"Resposta paginada incompleta: {name}; investigar paginação antes de usar")
            manifest.append({
                "arquivo": name, "fonte": "Siconfi DCA", "municipio": city,
                "ano": year, "url": url, "linhas": len(payload.get("items", [])),
                "hasMore": payload.get("hasMore"), "sha256": sha256(path),
            })
    return manifest


def fetch_json(name: str, url: str, session: requests.Session, refresh: bool) -> dict:
    path = RAW / name
    if refresh or not path.exists():
        response = session.get(url, timeout=120)
        response.raise_for_status()
        payload = response.json()
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    rows = len(payload) - 1 if isinstance(payload, list) else None
    return {"arquivo": name, "url": url, "linhas_dados": rows, "sha256": sha256(path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="substituir todos os arquivos brutos existentes")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    siconfi_manifest = read_siconfi_files(args.refresh)
    session = requests.Session()
    session.headers.update({"User-Agent": "P2-FSP-222036963-data-reproduction/1.0"})
    sidra_manifest = [fetch_json(name, url, session, args.refresh) for name, url in SIDRA_QUERIES.items()]
    eurostat = fetch_json("eurostat_gov_10dd_edpt1_be.json", EUROSTAT_URL, session, args.refresh)
    for entry in sidra_manifest:
        entry["fonte"] = "IBGE/SIDRA"
    eurostat["fonte"] = "Eurostat gov_10dd_edpt1"
    now = datetime.now(timezone.utc).isoformat()
    for entry in siconfi_manifest:
        entry["obtido_utc"] = now
    for entry in sidra_manifest + [eurostat]:
        entry["obtido_utc"] = now
    for name, rows in [
        ("manifest_siconfi.csv", siconfi_manifest),
        ("manifest_externos.csv", sidra_manifest + [eurostat]),
    ]:
        with (RAW / name).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    print(f"Siconfi: {len(siconfi_manifest)} arquivos anuais; linhas: {sum(x['linhas'] for x in siconfi_manifest)}")
    for entry in sidra_manifest:
        print(f"IBGE: {entry['arquivo']} — {entry['linhas_dados']} linhas")
    print(f"Eurostat: {eurostat['arquivo']} — SHA-256 {eurostat['sha256']}")


if __name__ == "__main__":
    main()
