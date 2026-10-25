"""Fase 3: autores, países (afiliaciones) y venue de los estudios de snowballing/control, vía OpenAlex.

Salida: revision/F3_analisis/metadatos_snowballing.csv  (raw en F2_busqueda/snowballing/raw/meta_*.json)
Uso:    python revision/F3_analisis/scripts/05_metadatos_snowballing.py
"""
import json
from pathlib import Path

import pandas as pd
import requests

REV = Path(__file__).resolve().parents[2]
SB = REV / "F2_busqueda" / "snowballing"
OUT = REV / "F3_analisis" / "metadatos_snowballing.csv"


def main():
    inc = pd.read_csv(SB / "snowball_incluidos.csv", keep_default_na=False, dtype=str)
    ids = [i.rsplit("/", 1)[-1] for i in inc["openalex_id"]]
    works = {}
    for k in range(0, len(ids), 50):
        f = SB / "raw" / f"meta_{k // 50:03d}.json"
        if not f.exists():
            r = requests.get("https://api.openalex.org/works", timeout=60, params={
                "filter": "openalex:" + "|".join(ids[k:k + 50]), "per_page": 50,
                "select": "id,authorships,primary_location"})
            r.raise_for_status()
            f.write_text(r.text, encoding="utf-8")
        for w in json.loads(f.read_text(encoding="utf-8"))["results"]:
            works[w["id"]] = w
    rows = []
    for s in inc.itertuples():
        w = works.get(s.openalex_id, {})
        auth = w.get("authorships", [])
        countries = sorted({c for a in auth for c in a.get("countries", [])})
        src = (w.get("primary_location") or {}).get("source") or {}
        rows.append(dict(id=s.id, authors=", ".join(a["author"]["display_name"] for a in auth),
                         countries_iso2=", ".join(countries), venue=src.get("display_name") or s.venue,
                         venue_type=src.get("type", "")))
    pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")
    df = pd.DataFrame(rows)
    print(len(df), "sin autores:", (df.authors == "").sum(), "sin país:", (df.countries_iso2 == "").sum())


if __name__ == "__main__":
    main()
