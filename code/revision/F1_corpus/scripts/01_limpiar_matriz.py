"""Fase 1 - Paso 1: limpieza y deduplicación de la matriz de extracción.

Lee la matriz original (v1_enviada/Systematic Review (1).xlsx), elimina filas
basura, normaliza valores, asigna IDs estables (P001...) y marca duplicados.

Salida: revision/F1_corpus/corpus_base.csv
Uso:    python revision/F1_corpus/scripts/01_limpiar_matriz.py
"""
from pathlib import Path
import re
import unicodedata

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "v1_enviada" / "Systematic Review (1).xlsx"
OUT = ROOT / "revision" / "F1_corpus" / "corpus_base.csv"

HEADER_ROW = 6          # fila (0-based) con los encabezados
COLUMNS = [
    "title", "authors", "countries", "venue", "doi", "dd_text", "datasets_text",
    "ml_text", "bio_text", "hyper_text", "metrics_text", "design_text",
    "conclusions_text", "summary_text", "year", "database", "quality_global",
    "c_accesible", "c_defect_density", "c_datasets", "c_ml_models",
    "c_eval_metrics", "r_english", "r_experimental_design", "r_bio_inspired",
    "r_hyperparameters",
]
YES_NO_COLS = [c for c in COLUMNS if c.startswith(("c_", "r_"))]


def norm_yes_no(v):
    if v is None or str(v).strip() == "":
        return "NA"
    s = unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode().strip().lower()
    if s.startswith("si") or s.startswith("yes"):
        return "Si"
    if s.startswith("no"):
        return "No"
    return "NA"


def norm_quality(v):
    if v is None or str(v).strip() == "":
        return "NA"
    s = str(v)
    if "+1" in s:
        return "+1"
    if "(0)" in s:
        return "0"
    if "1" in s:  # No (-1) / No (−1)
        return "-1"
    return "NA"


def norm_title(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def norm_doi(d):
    if d is None:
        return ""
    d = str(d).strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return "" if d in ("", "not provided", "none", "n/a") else d


def main():
    ws = openpyxl.load_workbook(SRC, read_only=True, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))[HEADER_ROW + 1:]
    records, dropped = [], []
    for i, r in enumerate(rows, start=HEADER_ROW + 2):  # número de fila Excel (1-based)
        if r[0] is None or str(r[0]).strip() == "":
            continue
        if str(r[0]).strip().lower().startswith("total:"):
            dropped.append((i, str(r[0])))
            continue
        rec = dict(zip(COLUMNS, r[: len(COLUMNS)]))
        rec["excel_row"] = i
        records.append(rec)

    df = pd.DataFrame(records)
    df.insert(0, "id", [f"P{n:03d}" for n in range(1, len(df) + 1)])
    for c in YES_NO_COLS:
        df[c] = df[c].map(norm_yes_no)
    df["quality_global"] = df["quality_global"].map(norm_quality)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["database"] = df["database"].fillna("NA").str.strip().str.replace("IEEE IET", "IEEE/IET")
    df["doi_norm"] = df["doi"].map(norm_doi)
    df["title_norm"] = df["title"].map(norm_title)
    df["inclusion_form_completed"] = df["c_defect_density"] != "NA"

    # Duplicados: se conserva la primera aparición
    df["duplicate_of"] = ""
    seen_doi, seen_title = {}, {}
    for idx, row in df.iterrows():
        key_doi, key_t = row["doi_norm"], row["title_norm"]
        if key_doi and key_doi in seen_doi:
            df.at[idx, "duplicate_of"] = seen_doi[key_doi]
        elif key_t in seen_title:
            df.at[idx, "duplicate_of"] = seen_title[key_t]
        else:
            if key_doi:
                seen_doi[key_doi] = row["id"]
            seen_title[key_t] = row["id"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")

    print(f"Filas descartadas (basura): {dropped}")
    print(f"Registros: {len(df)}")
    print(f"Duplicados: {(df['duplicate_of'] != '').sum()}")
    print(df.loc[df["duplicate_of"] != "", ["id", "duplicate_of", "title", "doi"]].to_string())
    print("Sin base de datos:", (df["database"] == "NA").sum())
    print("Sin año:", df["year"].isna().sum())
    print("Ficha de inclusión vacía:", (~df["inclusion_form_completed"]).sum())
    print("Quality:", df["quality_global"].value_counts().to_dict())


if __name__ == "__main__":
    main()
