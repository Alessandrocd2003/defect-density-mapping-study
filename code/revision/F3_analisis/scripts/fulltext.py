"""Lectura de la extracción a texto completo de los estudios añadidos por snowballing / conjunto de control.

La plantilla (F3_analisis/extraccion_texto_completo.xlsx) la genera 16_plantilla_extraccion.py y la completan
los revisores. Una fila se considera COMPLETA cuando tiene "Decisión final" (Incluir / Excluir).
Mientras no esté completa, el pipeline sigue usando título y resumen para ese estudio.
"""
import os
from pathlib import Path

import pandas as pd

# la variable de entorno FULLTEXT_XLSX permite probar con otra planilla sin tocar la real
PATH = Path(os.environ.get("FULLTEXT_XLSX") or Path(__file__).resolve().parents[1] / "extraccion_texto_completo.xlsx")
SHEETS = ("Extraccion_densidad", "Extraccion_recuento")

# encabezado visible en la plantilla -> nombre interno (alineado con la ficha original de la matriz)
COLUMNS = {
    "ID": "id", "Título": "titulo", "Autores": "autores", "Año": "anio", "Venue": "venue", "DOI": "doi",
    "Enlace": "enlace", "Tarea actual": "tarea_actual", "Revisor": "revisor", "Fecha": "fecha",
    "¿Accesible?": "c_accesible", "¿Predice un resultado de defectos de software?": "c_defectos",
    "¿Incluye datasets?": "c_datasets", "¿Incluye modelos de ML?": "c_ml_models",
    "¿Incluye métricas de evaluación?": "c_eval_metrics", "¿En inglés?": "r_english",
    "¿Diseño experimental?": "r_experimental_design", "¿Algoritmos bio-inspirados?": "r_bio_inspired",
    "¿Ajuste de hiperparámetros?": "r_hyperparameters", "Tarea confirmada": "tarea_confirmada",
    "Medida de tamaño (si es densidad)": "size_measure", "Datasets": "datasets_text",
    "Modelos de ML / estadísticos": "ml_text", "Algoritmos bio-inspirados y su rol": "bio_text",
    "Hiperparámetros (técnica de ajuste)": "hyper_text", "Métricas de evaluación": "metrics_text",
    "Diseño experimental / metodología": "design_text", "Conclusiones": "conclusions_text",
    "Q1 Objetivos claros": "q1", "Q2 Población y muestra": "q2", "Q3 Análisis de defectos y métricas": "q3",
    "Q4 Modelos de ML descritos": "q4", "Decisión final": "decision", "Motivo de exclusión": "motivo",
    "Notas": "notas",
}
TASKS = ["DENS", "COUNT", "CLASS", "EFFORT", "EMP", "REL", "LOCALIZ"]
EXCLUSION_CODES = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]


def load(path=PATH):
    """DataFrame (índice = ID) con las filas COMPLETAS de todas las hojas; vacío si la plantilla no existe."""
    if not Path(path).exists():
        return pd.DataFrame(columns=list(COLUMNS.values())).set_index("id")
    frames = []
    for sheet in SHEETS:
        try:
            df = pd.read_excel(path, sheet_name=sheet, keep_default_na=False, dtype=str)
        except ValueError:
            continue
        df = df.rename(columns=COLUMNS)[[c for c in COLUMNS.values() if c in df.rename(columns=COLUMNS).columns]]
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=list(COLUMNS.values())).set_index("id")
    df = pd.concat(frames, ignore_index=True)
    df = df[df["id"].str.strip() != ""].copy()
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    df["decision"] = df["decision"].str.capitalize()
    df["tarea_confirmada"] = df["tarea_confirmada"].str.upper().str.split().str[0].fillna("")
    df["motivo"] = df["motivo"].str.upper().str.extract(r"(E\d)", expand=False).fillna("")
    complete = df[df["decision"].isin(["Incluir", "Excluir"])]
    bad = complete[(complete.decision == "Excluir") & (complete.motivo == "")]
    if len(bad):
        raise ValueError(f"Extracción a texto completo: falta el motivo de exclusión en {list(bad.id)}")
    bad = complete[(complete.tarea_confirmada != "") & ~complete.tarea_confirmada.isin(TASKS)]
    if len(bad):
        raise ValueError(f"Extracción a texto completo: tarea no válida en {list(bad.id)}")
    return complete.set_index("id")
