"""Fase 2 / D11-(b): snowballing backward y forward (Wohlin, 2014) con OpenAlex.

Semillas: los 10 estudios de densidad (escenario A) + los 13 del conjunto de control.
Para cada semilla:
  - backward: obras que la semilla referencia (referenced_works)
  - forward:  obras que citan a la semilla (filter=cites:)
Los candidatos se filtran a 2014+ y se eliminan los que ya están en la matriz (por DOI o título).
Después se aplica un pre-filtro por palabras clave sobre título y resumen. Los que pasan van a
cribado manual (snowball_cribado.csv).

Uso: python revision/F2_busqueda/scripts/04_snowballing.py [--iter N] [--seeds archivo.csv]
Todas las respuestas de la API se guardan en snowballing/raw/ (reproducibilidad).
"""
import argparse
import json
import re
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests

REV = Path(__file__).resolve().parents[2]
SB = REV / "F2_busqueda" / "snowballing"
RAW = SB / "raw"
API = "https://api.openalex.org/works"
FIELDS = "id,doi,title,publication_year,primary_location,abstract_inverted_index,referenced_works,type"
MIN_YEAR = 2014

# Pre-filtro: el candidato debe tratar defectos/fallos de software con salida continua (densidad o recuento)
RE_OUTCOME = re.compile(r"(defect|fault|bug|error)s?[ -](density|densities|count|counts|number)|number of (defects|faults|bugs)"
                        r"|defects? per|faults? per|bugs? per|kloc", re.I)
RE_SOFTWARE = re.compile(r"software|program|source code|module|project|repositor|class(es)?\b|commit", re.I)


def norm_title(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def norm_doi(d):
    d = str(d or "").strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


def get(params, tag):
    """GET con caché en disco: si la respuesta ya existe, no se vuelve a consultar."""
    f = RAW / f"{tag}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    f.write_text(json.dumps(data), encoding="utf-8")
    time.sleep(0.2)
    return data


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    pos = sorted((p, word) for word, ps in inv.items() for p in ps)
    return " ".join(word for _, word in pos)


def by_ids(ids, tag):
    out = []
    ids = sorted(set(ids))
    for k in range(0, len(ids), 50):
        chunk = [i.rsplit("/", 1)[-1] for i in ids[k:k + 50]]
        out += get({"filter": "openalex:" + "|".join(chunk), "per_page": 50, "select": FIELDS},
                   f"{tag}_ids_{k // 50:03d}")["results"]
    return out


def citing(ids, tag):
    out = []
    ids = [i.rsplit("/", 1)[-1] for i in ids]
    for k in range(0, len(ids), 25):
        chunk = ids[k:k + 25]
        page = 1
        while True:
            d = get({"filter": f"cites:{'|'.join(chunk)},publication_year:>{MIN_YEAR - 1}",
                     "per_page": 200, "page": page, "select": FIELDS}, f"{tag}_cites_{k // 25:03d}_p{page}")
            out += d["results"]
            if page * 200 >= d["meta"]["count"]:
                break
            page += 1
    return out


def resolve_seeds(seeds, tag):
    works = []
    for s in seeds.itertuples():
        oa_id = getattr(s, "openalex_id", "")
        if oa_id:
            d = get({"filter": f"openalex:{oa_id.rsplit('/', 1)[-1]}", "select": FIELDS}, f"{tag}_seed_{s.seed_id}")
        elif s.doi:
            d = get({"filter": f"doi:{s.doi}", "select": FIELDS}, f"{tag}_seed_{s.seed_id}")
        else:
            d = get({"search": s.title, "per_page": 1, "select": FIELDS}, f"{tag}_seed_{s.seed_id}")
        res = d["results"]
        if not res:
            print(f"  ! semilla no resuelta: {s.seed_id} {s.title[:60]}")
            continue
        w = res[0]
        if not s.doi and not oa_id and norm_title(w["title"]) != norm_title(s.title):
            print(f"  ? semilla {s.seed_id}: título distinto en OpenAlex -> {w['title'][:70]}")
        w["seed_id"] = s.seed_id
        works.append(w)
    return works


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", type=int, default=1)
    ap.add_argument("--seeds", default=str(SB / "semillas_iter1.csv"))
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    tag = f"it{a.iter}"

    seeds = pd.read_csv(a.seeds, keep_default_na=False, dtype=str)
    seed_works = resolve_seeds(seeds, tag)
    seed_ids = {w["id"] for w in seed_works}
    print(f"Semillas resueltas: {len(seed_works)}/{len(seeds)}")

    refs = {r: w["seed_id"] for w in seed_works for r in w.get("referenced_works", [])}
    backward = by_ids(list(refs), f"{tag}_bw")
    forward = citing(list(seed_ids), tag)
    print(f"Backward: {len(backward)} referencias · Forward: {len(forward)} citas")

    matrix = pd.read_excel(REV / "F1_corpus" / "extraction_matrix_v2.xlsx", sheet_name="Corpus_v2",
                           keep_default_na=False, dtype=str)
    known_doi = set(matrix["doi"].map(norm_doi)) - {""}
    known_t = set(matrix["title"].map(norm_title))
    known_oa = set()
    for k in range(1, a.iter):  # candidatos ya evaluados en iteraciones previas
        p = pd.read_csv(SB / f"snowball_candidatos_it{k}.csv", keep_default_na=False, dtype=str)
        known_oa |= set(p["openalex_id"])
        known_doi |= set(p["doi"]) - {""}
        known_t |= set(p["title"].map(norm_title))

    rows, seen = [], set()
    for direction, works in (("backward", backward), ("forward", forward)):
        for w in works:
            if w["id"] in seen or w["id"] in seed_ids or w["id"] in known_oa:
                continue
            seen.add(w["id"])
            year = w.get("publication_year") or 0
            doi, title = norm_doi(w.get("doi")), w.get("title") or ""
            ab = abstract(w)
            text = f"{title} {ab}"
            in_matrix = (doi and doi in known_doi) or norm_title(title) in known_t
            src = (w.get("primary_location") or {}).get("source") or {}
            rows.append(dict(
                openalex_id=w["id"], doi=doi, title=title, year=year, venue=src.get("display_name", ""),
                tipo=w.get("type", ""), direccion=direction, iteracion=a.iter,
                semilla=refs.get(w["id"], "") if direction == "backward" else "cita a semilla(s)",
                ya_en_matriz=bool(in_matrix), anio_ok=year >= MIN_YEAR,
                prefiltro=bool(RE_OUTCOME.search(text) and RE_SOFTWARE.search(text)),
                tiene_resumen=bool(ab), resumen=ab[:1500]))
    cand = pd.DataFrame(rows)
    out = SB / f"snowball_candidatos_it{a.iter}.csv"
    cand.to_csv(out, index=False, encoding="utf-8-sig")

    nuevos = cand[~cand.ya_en_matriz & cand.anio_ok]
    print(f"Candidatos únicos: {len(cand)} · ya en matriz: {int(cand.ya_en_matriz.sum())} · "
          f"<{MIN_YEAR}: {int((~cand.anio_ok).sum())} · nuevos {MIN_YEAR}+: {len(nuevos)} · "
          f"pasan pre-filtro: {int(nuevos.prefiltro.sum())} · sin resumen: {int((~nuevos.tiene_resumen).sum())}")


if __name__ == "__main__":
    main()
