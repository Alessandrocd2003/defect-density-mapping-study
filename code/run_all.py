"""Reproduces the screening corpus, snowballing coding, analyses, tables and figures.

Run from this folder:  python run_all.py
Steps 04 and 05 query the OpenAlex API (responses are cached in revision/F2_busqueda/snowballing/raw/).
OpenAlex metadata evolve over time, so re-downloaded abstracts or affiliations may differ slightly from the
ones used in the paper (retrieved on 2026-10-24). Manual decisions (domain, task, snowballing screening) are
inputs in the CSV files and are not recomputed.
"""
import subprocess
import sys

STEPS = [
    ["revision/F1_corpus/scripts/01_limpiar_matriz.py"],
    ["revision/F1_corpus/scripts/02_construir_corpus.py"],
    ["revision/F2_busqueda/scripts/03_metricas_busqueda.py"],
    ["revision/F2_busqueda/scripts/04_snowballing.py", "--iter", "1", "--seeds", "revision/F2_busqueda/snowballing/semillas_iter1.csv"],
    ["revision/F2_busqueda/scripts/04_snowballing.py", "--iter", "2", "--seeds", "revision/F2_busqueda/snowballing/semillas_iter2.csv"],
    ["revision/F2_busqueda/scripts/04_snowballing.py", "--iter", "3", "--seeds", "revision/F2_busqueda/snowballing/semillas_iter3.csv"],
    ["revision/F3_analisis/scripts/05_metadatos_snowballing.py"],
    ["revision/F3_analisis/scripts/06_codificar_extraccion.py"],
    ["revision/F3_analisis/scripts/07_analisis_mq.py"],
    ["revision/F3_analisis/scripts/09_actualizar_excel_mq.py"],
    ["revision/F3_analisis/scripts/10_figuras_estilo_excel.py"],
]
for step in STEPS:
    print(">>", " ".join(step), flush=True)
    subprocess.run([sys.executable, *step], check=True)
