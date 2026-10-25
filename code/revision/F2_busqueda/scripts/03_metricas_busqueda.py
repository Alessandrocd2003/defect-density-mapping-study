"""Fase 2: precisión de la cadena de búsqueda por base de datos y recall frente al conjunto de control.

Entradas: revision/F1_corpus/extraction_matrix_v2.xlsx, revision/F2_busqueda/conjunto_control.csv
Salida:   revision/F2_busqueda/metricas_busqueda.md
Uso:      python revision/F2_busqueda/scripts/03_metricas_busqueda.py
"""
from pathlib import Path

import pandas as pd

REV = Path(__file__).resolve().parents[2]
MATRIX = REV / "F1_corpus" / "extraction_matrix_v2.xlsx"
CONTROL = REV / "F2_busqueda" / "conjunto_control.csv"
OUT = REV / "F2_busqueda" / "metricas_busqueda.md"


def pct(a, b):
    return f"{a} ({100 * a / b:.1f} %)" if b else "0"


def main():
    df = pd.read_excel(MATRIX, sheet_name="Corpus_v2", keep_default_na=False, dtype=str)
    df = df[(df["exclusion"] != "DUP") & (df["fuente"] == "busqueda_bd")]  # solo lo que recuperó la cadena
    in_dom = df["dominio"].isin(["SE_DEFECT_PRED", "SE_RELIABILITY"])
    incl = df["incluido_C_amplio"] == "True"
    dens = df["incluido_A_estricto"] == "True"

    rows = []
    for db, g in df.groupby("database"):
        idx = g.index
        rows.append((db, len(g), pct(int(in_dom[idx].sum()), len(g)), pct(int(incl[idx].sum()), len(g)),
                     int(dens[idx].sum()), pct(int((g["dominio"] == "NO_SE").sum()), len(g))))
    rows.append(("**Total**", len(df), pct(int(in_dom.sum()), len(df)), pct(int(incl.sum()), len(df)),
                 int(dens.sum()), pct(int((df["dominio"] == "NO_SE").sum()), len(df))))

    ctrl = pd.read_csv(CONTROL, keep_default_na=False, dtype=str)
    found = ctrl["id_en_matriz"] != ""

    lines = ["# Métricas de la estrategia de búsqueda (generado por 03_metricas_busqueda.py)", "",
             "## Precisión por base de datos (registros únicos, sin duplicados)", "",
             "| Base | Recuperados | En dominio | Incluidos (C) | Densidad (A) | Fuera de SE (E6) |",
             "|---|---|---|---|---|---|"]
    lines += ["| " + " | ".join(map(str, r)) + " |" for r in rows]
    lines += ["", "## Recall frente al conjunto de control", "",
              f"Estudios de control: {len(ctrl)} · encontrados en la matriz: {int(found.sum())} · "
              f"**recall = {100 * found.mean():.0f} %**", "",
              "| Control | Año | Venue | Indexación | En matriz |", "|---|---|---|---|---|"]
    lines += [f"| {r.control_id} | {r.anio} | {r.venue} | {r.editorial_indexacion} | {r.id_en_matriz or '**no**'} |"
              for r in ctrl.itertuples()]
    by_db = ctrl.assign(en=found).groupby("editorial_indexacion")["en"].agg(["sum", "count"])
    lines += ["", "Por indexación principal: " +
              "; ".join(f"{k}: {int(v['sum'])}/{int(v['count'])}" for k, v in by_db.iterrows())]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
