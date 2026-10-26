#!/usr/bin/env python3
"""Fetch OpenAlex metadata/abstracts for the DOI-verified bibliography."""
from __future__ import annotations
import csv, json, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"data/bibliometria/corpus_verificado.csv"
OUT=ROOT/"data/bibliometria/resumos_openalex.csv"
RAW=ROOT/"data/bibliometria/openalex_responses.jsonl"

def abstract_from_index(idx):
    if not idx: return ""
    n=max(pos for positions in idx.values() for pos in positions)+1
    words=[None]*n
    for word, positions in idx.items():
        for pos in positions: words[pos]=word
    return " ".join(w for w in words if w)

def fetch(row):
    doi=row["doi"].strip()
    url="https://api.openalex.org/works/https://doi.org/"+doi
    headers={"User-Agent":"P2-public-finance-literature-review/1.0 (educational research)"}
    for attempt in range(4):
        try:
            r=requests.get(url,headers=headers,timeout=25)
            if r.status_code==404: return row, {"status":"not_found","doi":doi}
            r.raise_for_status(); w=r.json()
            src=(w.get("primary_location") or {}).get("source") or {}
            result={"status":"ok","doi":doi,"openalex_id":w.get("id"),"title":w.get("title"),"year":w.get("publication_year"),"type":w.get("type"),"journal":src.get("display_name"),"abstract":abstract_from_index(w.get("abstract_inverted_index"))}
            return row,result
        except Exception as e:
            if attempt==3: return row,{"status":"error","doi":doi,"error":str(e)}
            time.sleep(1.5*(attempt+1))

def main():
    with IN.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=80: raise SystemExit(f"Expected 80 verified records, got {len(rows)}")
    results={}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs=[ex.submit(fetch,r) for r in rows]
        for fut in as_completed(futs):
            row,res=fut.result(); results[row["doi"].lower()]=(row,res)
    out=[]; raw=[]
    for row in rows:
        r0,res=results[row["doi"].lower()]
        out.append({"citation_key":row["citation_key"],"doi":row["doi"],"candidate_title":row["title"],"candidate_year":row["year"],"topic":row.get("topic",""),"openalex_title":res.get("title",""),"openalex_year":res.get("year",""),"openalex_type":res.get("type",""),"openalex_journal":res.get("journal",""),"abstract":res.get("abstract",""),"abstract_status":res.get("status",""),"error":res.get("error","")})
        raw.append(json.dumps(res,ensure_ascii=False))
    with OUT.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    RAW.write_text("\n".join(raw)+"\n",encoding="utf-8")
    print(f"records={len(out)} abstract_present={sum(bool(r['abstract']) for r in out)} errors={sum(r['abstract_status']=='error' for r in out)} not_found={sum(r['abstract_status']=='not_found' for r in out)} output={OUT}")
if __name__=="__main__": main()
