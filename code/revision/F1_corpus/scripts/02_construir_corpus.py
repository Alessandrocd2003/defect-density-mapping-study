"""Fase 1 - Paso 2: aplicar criterios, reconstruir el flujo PRISMA y exportar la matriz v2.

Entradas (en revision/F1_corpus/):
  corpus_base.csv            <- 01_limpiar_matriz.py
  clasificacion_dominio.csv  <- clasificación manual de dominio (editable por el equipo)
  clasificacion_tarea.csv    <- clasificación manual de tarea predictiva (editable)

Salidas:
  extraction_matrix_v2.xlsx  (corpus con decisiones, escenarios, PRISMA, muestras para kappa y calidad)
  prisma_resumen.md

Uso: python revision/F1_corpus/scripts/02_construir_corpus.py
"""
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE.parent / "F3_analisis" / "scripts"))
import fulltext  # noqa: E402  extracción a texto completo de los estudios de snowballing / control
OUT_XLSX = BASE / "extraction_matrix_v2.xlsx"
OUT_MD = BASE / "prisma_resumen.md"
SB = BASE.parent / "F2_busqueda" / "snowballing"   # D11-(b): snowballing + conjunto de control

IN_DOMAIN = {"SE_DEFECT_PRED", "SE_RELIABILITY"}
SEED = 2026
# D12: tareas de los estudios de snowballing que entran al escenario C (A y B los incluyen siempre)
SNOWBALL_TASKS_IN_C = {"DENS"}

# Escenarios de corpus final (decisión D2 del acta)
SCENARIOS = {
    "A_estricto": {"DENS"},                       # solo densidad de defectos continua
    "B_continuo": {"DENS", "COUNT"},              # salidas continuas (densidad + recuento), como los "continuous studies" de Hall et al.
    "C_amplio": {"DENS", "COUNT", "EFFORT", "CLASS", "EMP", "REL", "LOCALIZ"},  # toda la predicción de defectos primaria
}

EXCLUSION_LABELS = {
    "DUP": "Duplicado",
    "E6": "E6: fuera del dominio de ingeniería de software",
    "E2": "E2: software, pero no aborda defectos/densidad",
    "PEND": "Pendiente: ficha de inclusión sin completar",
    "E1": "E1: no accesible",
    "E7": "E7: estudio secundario (revisión/encuesta/metodológico)",
    "E3": "E3: sin datasets",
    "E4": "E4: sin modelos de ML",
    "E5": "E5: sin métricas de evaluación",
}


def exclusion_code(r):
    """Primer criterio que falla, en el orden del flujo de selección."""
    if r["duplicate_of"]:
        return "DUP"
    if r["dominio"] == "NO_SE":
        return "E6"
    if r["dominio"] == "SE_OTHER":
        return "E2"
    if r["es_secundario"] == "Si":
        return "E7"
    if r["c_defect_density"] == "NA":
        return "PEND"
    if r["c_accesible"] == "No":
        return "E1"
    if r["c_datasets"] == "No":
        return "E3"
    if r["c_ml_models"] == "No":
        return "E4"
    if r["c_eval_metrics"] == "No":
        return "E5"
    return ""


def main():
    # keep_default_na=False: "NA" es un valor propio (no evaluado), no un vacío
    read = lambda f: pd.read_csv(BASE / f, keep_default_na=False, dtype=str)
    base, dom, task = read("corpus_base.csv"), read("clasificacion_dominio.csv"), read("clasificacion_tarea.csv")
    df = (base.merge(dom, on="id", how="left")
              .merge(task, on="id", how="left"))
    df["es_secundario"] = df["es_secundario"].fillna("No")
    df["tarea"] = df["tarea"].fillna("")
    assert df["dominio"].notna().all(), "Hay registros sin dominio asignado"

    df["exclusion"] = df.apply(exclusion_code, axis=1)
    df["exclusion_motivo"] = df["exclusion"].map(EXCLUSION_LABELS).fillna("")
    df["fuente"] = "busqueda_bd"
    for name, tasks in SCENARIOS.items():
        df[f"incluido_{name}"] = (df["exclusion"] == "") & df["tarea"].isin(tasks)

    # --- Estudios añadidos por snowballing / conjunto de control -------------
    sb = pd.read_csv(SB / "snowball_incluidos.csv", keep_default_na=False, dtype=str)
    sb_rows = pd.DataFrame({
        "id": sb["id"], "title": sb["title"], "year": sb["year"], "venue": sb["venue"], "doi": sb["doi"],
        "database": sb["fuente"].map({"snowballing": "Snowballing", "conjunto_control": "Conjunto de control"}),
        "dominio": "SE_DEFECT_PRED", "confianza": sb["confianza"], "tarea": sb["tarea"],
        "confianza_tarea": sb["confianza"], "es_secundario": "No", "exclusion": "", "exclusion_motivo": "",
        "nota": sb["motivo"] + " · Incluido por título/resumen; requiere verificación a texto completo",
        "fuente": sb["fuente"], "duplicate_of": "",
    })
    # Extracción a texto completo (si existe): confirma o corrige la tarea, o excluye el estudio
    ftx = fulltext.load()
    for i, r in sb_rows.iterrows():
        if r["id"] not in ftx.index:
            continue
        f = ftx.loc[r["id"]]
        if f["tarea_confirmada"]:
            sb_rows.at[i, "tarea"] = f["tarea_confirmada"]
        sb_rows.at[i, "confianza_tarea"] = "alta"
        sb_rows.at[i, "nota"] = sb_rows.at[i, "nota"].split(" · ")[0] + " · Verificado a texto completo"
        if f["decision"] == "Excluir":
            sb_rows.at[i, "exclusion"] = f["motivo"]
            sb_rows.at[i, "exclusion_motivo"] = EXCLUSION_LABELS.get(f["motivo"], f["motivo"])
    ok = sb_rows["exclusion"] == ""
    sb_rows["incluido_A_estricto"] = ok & (sb_rows["tarea"] == "DENS")
    sb_rows["incluido_B_continuo"] = ok & sb_rows["tarea"].isin({"DENS", "COUNT"})
    sb_rows["incluido_C_amplio"] = ok & sb_rows["tarea"].isin(SNOWBALL_TASKS_IN_C)
    crib = pd.concat(pd.read_csv(f, keep_default_na=False, dtype=str)
                     for f in sorted(SB.glob("snowball_cribado_it*.csv")))
    db_df = df
    df = pd.concat([df, sb_rows], ignore_index=True).fillna("")

    # --- Flujo PRISMA -------------------------------------------------------
    n = len(db_df)
    df_all, df = df, db_df  # el flujo de búsqueda se calcula solo con la matriz original
    step = lambda code: int((df["exclusion"] == code).sum())
    by_db = df.groupby("database").size().to_dict()
    flow = [
        ("Registros identificados (matriz consolidada)", n),
        ("  por base de datos", by_db),
        ("Duplicados eliminados", step("DUP")),
        ("Registros cribados", n - step("DUP")),
        ("Excluidos E6 (fuera de dominio SE)", step("E6")),
        ("Excluidos E2 (SE sin foco en defectos)", step("E2")),
        ("Candidatos en dominio (predicción de defectos / fiabilidad)", n - step("DUP") - step("E6") - step("E2")),
        ("Excluidos E7 (secundarios)", step("E7")),
        ("Pendientes de evaluación (ficha vacía)", step("PEND")),
        ("Excluidos E1 (no accesible)", step("E1")),
        ("Excluidos E3/E4/E5 (sin datasets / ML / métricas)", step("E3") + step("E4") + step("E5")),
        ("Elegibles (estudios primarios que cumplen criterios)", int((df["exclusion"] == "").sum())),
        ("Snowballing: candidatos 2014+ cribados (3 iteraciones)", len(crib)),
        ("  por iteración", crib.groupby("iteracion").size().to_dict()),
        ("Snowballing: incluidos por título/resumen", int((crib["decision"] == "INCL").sum())),
        ("  por tarea", crib.loc[crib["decision"] == "INCL", "tarea"].value_counts().to_dict()),
        ("Snowballing: pendientes de verificar", int((crib["decision"] == "VERIFICAR").sum())),
        ("Conjunto de control no recuperado por la búsqueda (añadido)", int((sb["fuente"] == "conjunto_control").sum())),
        ("Snowballing/control verificados a texto completo", int(sb_rows["id"].isin(ftx.index).sum())),
        ("  de ellos excluidos a texto completo", int((sb_rows["exclusion"] != "").sum())),
    ]
    elig_db = df[df["exclusion"] == ""]
    df = df_all
    for name in SCENARIOS:
        flow.append((f"INCLUIDOS escenario {name}", int(df[f"incluido_{name}"].sum())))
    flow.append(("  de ellos por snowballing/control (escenario C)",
                 int((df["incluido_C_amplio"] & (df["fuente"] != "busqueda_bd")).sum())))

    elig = df[df["incluido_C_amplio"]]
    tasks_elig = elig["tarea"].value_counts().to_dict()
    pend_dom = df.loc[df["exclusion"] == "PEND", ["id", "title", "dominio", "tarea"]]

    # --- Muestra estratificada para kappa (≈20 %), solo registros de la búsqueda --
    pool = df[(df["exclusion"] != "DUP") & (df["fuente"] == "busqueda_bd")]
    sample = pd.concat(g.sample(frac=0.2, random_state=SEED) for _, g in pool.groupby("dominio"))
    kappa = sample[["id", "title", "venue", "year"]].copy()
    for rev in ("R1", "R2"):
        kappa[f"{rev}_dominio (NO_SE/SE_OTHER/SE_DEFECT_PRED/SE_RELIABILITY)"] = ""
        kappa[f"{rev}_incluir (Si/No)"] = ""
        kappa[f"{rev}_tarea (DENS/COUNT/EFFORT/CLASS/EMP/REL/SEC)"] = ""
    kappa = kappa.sort_values("id")

    # --- Instrumento de calidad (4 ítems) para elegibles ----------------------
    qa = elig[["id", "title", "tarea", "quality_global"]].copy()
    for q in ("Q1_objetivos", "Q2_poblacion_muestra", "Q3_analisis_densidad_metricas", "Q4_modelos_ML_descritos"):
        qa[f"{q} (-1/0/+1)"] = ""
    qa["total (suma)"] = ""

    # Las hojas Muestra_kappa y Calidad_4items las completa el equipo a mano: al regenerar se conserva lo ya llenado
    def keep_filled(new, sheet):
        if not OUT_XLSX.exists():
            return new
        try:
            old = pd.read_excel(OUT_XLSX, sheet_name=sheet, keep_default_na=False, dtype=str).set_index("id")
        except ValueError:
            return new
        manual = [c for c in new.columns if c in old.columns and c not in ("id", "title", "venue", "year", "tarea", "quality_global")]
        new = new.set_index("id")
        for c in manual:
            filled = old[c][old[c].str.strip() != ""]
            new.loc[new.index.intersection(filled.index), c] = filled
        return new.reset_index()

    kappa = keep_filled(kappa, "Muestra_kappa")
    qa = keep_filled(qa, "Calidad_4items")

    # --- Exportar -----------------------------------------------------------
    cols_front = ["id", "fuente", "title", "year", "database", "venue", "doi", "dominio", "confianza",
                  "tarea", "confianza_tarea", "es_secundario", "exclusion", "exclusion_motivo",
                  *[f"incluido_{s}" for s in SCENARIOS], "nota", "quality_global",
                  "c_accesible", "c_defect_density", "c_datasets", "c_ml_models", "c_eval_metrics",
                  "r_english", "r_experimental_design", "r_bio_inspired", "r_hyperparameters",
                  "duplicate_of", "excel_row"]
    rest = [c for c in df.columns if c not in cols_front and c not in ("doi_norm", "title_norm")]
    df = df[cols_front + rest]

    flow_df = pd.DataFrame([(k, str(v)) for k, v in flow], columns=["Paso", "n"])
    excl_df = (df["exclusion_motivo"].replace("", "Elegible").value_counts()
               .rename_axis("Decisión").reset_index(name="n"))
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="Corpus_v2", index=False)
        flow_df.to_excel(xw, sheet_name="PRISMA", index=False)
        excl_df.to_excel(xw, sheet_name="Decisiones_resumen", index=False)
        for name in SCENARIOS:
            df[df[f"incluido_{name}"]].to_excel(xw, sheet_name=f"Incluidos_{name}"[:31], index=False)
        pend_dom.to_excel(xw, sheet_name="Pendientes_ficha", index=False)
        kappa.to_excel(xw, sheet_name="Muestra_kappa", index=False)
        qa.to_excel(xw, sheet_name="Calidad_4items", index=False)

    lines = ["# Flujo PRISMA reconstruido (generado por 02_construir_corpus.py)\n",
             "| Paso | n |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in flow]
    lines += ["", f"**Tareas entre elegibles de la búsqueda:** {elig_db['tarea'].value_counts().to_dict()}",
              "", f"**Tareas en el corpus C final:** {tasks_elig}", "",
              f"**Pendientes por dominio:** {pend_dom['dominio'].value_counts().to_dict()}",
              "", f"**Muestra kappa:** {len(kappa)} registros (semilla {SEED})"]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
