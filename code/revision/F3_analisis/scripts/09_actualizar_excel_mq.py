"""Actualiza Systematic_Review_MQ_Analysis.xlsx con el corpus definitivo, conservando el diseño de sus gráficos.

Se edita el paquete XML directamente (openpyxl no conserva gráficos ni el mapa chartEx de MQ6):
  - hojas MQ: se reescriben los datos (título, encabezado, filas, notas) con cadenas en línea
  - gráficos: se actualizan rangos (<c:f>), cachés (strCache/numCache) y colores por punto (dPt)
  - mapa MQ6: se actualizan los nombres definidos que usa (_xlchart.v5.*)
  - hoja Data: estudios de los corpus C y B con su codificación; nueva hoja Cribado_busqueda (367 registros)
El estilo de los gráficos (colores del tema, degradados, sombras, etiquetas) no se toca.

Entrada: v1_enviada/Systematic_Review_MQ_Analysis.xlsx + resultados de F1–F3
Salida:  Systematic_Review_MQ_Analysis_v2.xlsx (en la carpeta raíz de Revisión)
Uso:     python revision/F3_analisis/scripts/09_actualizar_excel_mq.py
"""
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
REV = ROOT / "revision"
SRC = ROOT / "v1_enviada" / "Systematic_Review_MQ_Analysis.xlsx"
OUT = ROOT / "Systematic_Review_MQ_Analysis_v2.xlsx"
TASKS = [("DENS", "Defect density"), ("COUNT", "Defect count"), ("CLASS", "Classification"),
         ("EFFORT", "Effort-aware"), ("OTHER", "Other")]
COLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ---------------------------------------------------------------- celdas ---
def cell(ref, v, s=None):
    st = f' s="{s}"' if s is not None else ""
    if v is None or v == "":
        return f'<c r="{ref}"{st}/>'
    if isinstance(v, str) and v.startswith("="):
        return f'<c r="{ref}"{st}><f>{escape(v[1:])}</f></c>'
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f'<c r="{ref}"{st}><v>{v}</v></c>'
    return f'<c r="{ref}"{st} t="inlineStr"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>'


def mq_sheet_data(title, header, rows, notes, extra_blocks=(), total=False):
    """Título A1 (s=4, fusionado A1:C1), encabezado fila 3 (s=1), datos desde fila 4 (s=2), notas (s=3).
    extra_blocks: [(fila_inicio, encabezado, filas)] tablas adicionales debajo."""
    out = [f'<row r="1">{cell("A1", title, 4)}{cell("B1", "", 5)}{cell("C1", "", 5)}</row>',
           '<row r="3">' + "".join(cell(f"{COLS[i]}3", h, 1) for i, h in enumerate(header)) + "</row>"]
    r = 4
    for row in rows:
        out.append(f'<row r="{r}">' + "".join(cell(f"{COLS[i]}{r}", v, 2) for i, v in enumerate(row)) + "</row>")
        r += 1
    last = r - 1
    if total:
        out.append(f'<row r="{r}">{cell(f"A{r}", "Total", 1)}{cell(f"B{r}", f"=SUM(B4:B{last})", 1)}</row>')
        r += 1
    for n in notes:
        out.append(f'<row r="{r}">{cell(f"A{r}", n, 3)}</row>')
        r += 1
    for start, hdr, rws in extra_blocks:
        r = max(r + 1, start)
        out.append(f'<row r="{r}">' + "".join(cell(f"{COLS[i]}{r}", h, 1) for i, h in enumerate(hdr)) + "</row>")
        r += 1
        for row in rws:
            out.append(f'<row r="{r}">' + "".join(cell(f"{COLS[i]}{r}", v, 2) for i, v in enumerate(row)) + "</row>")
            r += 1
    width = max([len(header)] + [len(h) for _, h, _ in extra_blocks])
    return "".join(out), last, f"A1:{COLS[width - 1]}{r}"


def replace_sheet(xml, sheet_data, dim, widths):
    xml = re.sub(r"<sheetData>.*</sheetData>|<sheetData/>", f"<sheetData>{sheet_data}</sheetData>", xml, flags=re.S)
    xml = re.sub(r'<dimension ref="[^"]+"/>', f'<dimension ref="{dim}"/>', xml)
    cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths))
    return re.sub(r"<cols>.*?</cols>", f"<cols>{cols}</cols>", xml, flags=re.S)


# --------------------------------------------------------------- gráficos ---
def str_cache(vals):
    pts = "".join(f'<c:pt idx="{i}"><c:v>{escape(str(v))}</c:v></c:pt>' for i, v in enumerate(vals))
    return f'<c:strCache><c:ptCount val="{len(vals)}"/>{pts}</c:strCache>'


def num_cache(vals):
    pts = "".join(f'<c:pt idx="{i}"><c:v>{v}</c:v></c:pt>' for i, v in enumerate(vals))
    return f'<c:numCache><c:formatCode>General</c:formatCode><c:ptCount val="{len(vals)}"/>{pts}</c:numCache>'


def update_chart(xml, sheet, start, cats, vals):
    n = len(cats)
    end = start + n - 1
    for col in ("A", "B"):
        xml = re.sub(rf"({re.escape(sheet)}!\${col}\${start}:\${col}\$)\d+", rf"\g<1>{end}", xml)
    xml = re.sub(r"(<c:cat>.*?)<c:strCache>.*?</c:strCache>", lambda m: m.group(1) + str_cache(cats), xml, flags=re.S)
    xml = re.sub(r"(<c:val>.*?)<c:numCache>.*?</c:numCache>", lambda m: m.group(1) + num_cache(vals), xml, flags=re.S)
    # colores por punto: se conservan los existentes y se replican cíclicamente si hay más puntos
    dpts = re.findall(r"<c:dPt>.*?</c:dPt>", xml, flags=re.S)
    if dpts:
        base = [re.sub(r"<c:extLst>.*?</c:extLst>", "", d, flags=re.S) for d in dpts]
        new = []
        for i in range(n):
            d = dpts[i] if i < len(dpts) else base[i % len(base)]
            new.append(re.sub(r'<c:idx val="\d+"/>', f'<c:idx val="{i}"/>', d, count=1))
        first = xml.find(dpts[0])
        last = xml.find(dpts[-1]) + len(dpts[-1])
        xml = xml[:first] + "".join(new) + xml[last:]
    return xml


def set_title(xml, old, new):
    return xml.replace(f"<a:t>{old}</a:t>", f"<a:t>{escape(new)}</a:t>")


# ------------------------------------------------------------------ datos ---
def load():
    d = pd.read_csv(REV / "F3_analisis" / "corpus_codificado.csv", keep_default_na=False, dtype=str)
    m = pd.read_excel(REV / "F1_corpus" / "extraction_matrix_v2.xlsx", sheet_name="Corpus_v2",
                      keep_default_na=False, dtype=str)
    d = d.merge(m[["id", "title", "doi", "database"]], on="id", how="left")
    d["tg"] = d["tarea"].where(d["tarea"].isin([t for t, _ in TASKS[:-1]]), "OTHER")
    return d, m


def counts(df, col, sep="; "):
    s = df[["id", col]].assign(**{col: df[col].str.split(sep)}).explode(col)
    s = s[s[col].astype(bool)]
    return s.groupby(col)["id"].nunique().sort_values(ascending=False), s


def by_task(df, col):
    tot, ex = counts(df, col)
    ex = ex.merge(df[["id", "tg"]], on="id")
    ct = pd.crosstab(ex[col], ex["tg"])
    return [[k, int(v)] + [int(ct.at[k, t]) if t in ct.columns else 0 for t, _ in TASKS] for k, v in tot.items()]


def main():
    d, m = load()
    C = d[d["en_C"] == "True"]
    B = d[d["en_B"] == "True"]
    N = len(C)
    task_hdr = [f"{lab} (n={int((C.tg == t).sum())})" for t, lab in TASKS]
    note_c = f"Corpus C (mapeo): N = {N} estudios. Cada estudio cuenta una vez por categoría."
    zin = zipfile.ZipFile(SRC)
    files = {n: zin.read(n) for n in zin.namelist()}
    txt = lambda n: files[n].decode("utf-8")
    sheets, charts = {}, {}

    # MQ1 — fuentes (registros identificados, únicos e incluidos)
    mm = m[m.fuente == "busqueda_bd"]
    dbs = ["SpringerLink", "ACM Digital Library", "IEEE/IET Electronic Library", "Scopus"]
    rows = [[db, int((mm.database == db).sum()), int(((mm.database == db) & (mm.exclusion != "DUP")).sum()),
             int(((C.database == db)).sum())] for db in dbs]
    sd = mq_sheet_data("MQ1: ¿Cuántos artículos hay por base de datos?",
                       ["Database", "# Papers (identificados)", "# Únicos", "# Incluidos en C"], rows,
                       [f"Identificados: {len(mm)} · únicos: {int((mm.exclusion != 'DUP').sum())} · "
                        f"incluidos en C: {N} (+{int((C.fuente == 'snowballing').sum())} por snowballing, "
                        f"+{int((C.fuente == 'conjunto_control').sum())} del conjunto de control)."], total=True)
    sheets["sheet2.xml"] = (sd, [36, 22, 12, 16])
    charts["chart1.xml"] = ("MQ1_Database", 4, [r[0] for r in rows], [r[1] for r in rows])

    # MQ2 — flujo de selección + corpus C por tarea
    flow = [("Identified (367)", 367), ("Screened, unique (365)", 365), ("In domain (114)", 114),
            ("Eligible from search (94)", 94), (f"Included in C ({N})", N)]
    tasks = [(lab, int((C.tg == t).sum())) for t, lab in TASKS]
    sd = mq_sheet_data("MQ2: Revisados vs. seleccionados (flujo PRISMA)", ["Categoria", "# Papers"],
                       [list(x) for x in flow],
                       ["E6 fuera de software: 149 · E2 software sin defectos: 102 · E7 secundarios: 11 · "
                        "pendientes: 5 · E4 sin ML: 4 · +18 de densidad por snowballing/control."],
                       extra_blocks=[(11, ["Corpus C por tipo de tarea", "# Papers"], [list(x) for x in tasks])])
    sheets["sheet3.xml"] = (sd, [44, 16])
    charts["chart2.xml"] = ("MQ2_Reviewed_vs_Selected", 4, [x[0] for x in flow], [x[1] for x in flow])
    charts["chart3.xml"] = ("MQ2_Reviewed_vs_Selected", 12, [x[0] for x in tasks], [x[1] for x in tasks])

    # MQ3 — autores (≥3 estudios)
    au, _ = counts(C, "autores")
    top = au[au >= 3]
    sd = mq_sheet_data("MQ3: Autores más frecuentes (≥ 3 estudios)", ["Author", "# Papers"],
                       [[k, int(v)] for k, v in top.items()],
                       [note_c, f"Autores distintos: {len(au)}. Frecuencia de autoría (no de citación)."])
    sheets["sheet4.xml"] = (sd, [36, 12])
    charts["chart4.xml"] = ("MQ3_Authors", 4, list(top.index), [int(v) for v in top.values])

    # MQ4 — venues (≥2 estudios)
    vn, _ = counts(C[C.venue != ""], "venue", sep="\x00")
    vtop = vn[vn >= 2]
    sd = mq_sheet_data("MQ4: Revistas / venues más frecuentes (≥ 2 estudios)", ["Journal / Venue", "# Papers"],
                       [[k, int(v)] for k, v in vtop.items()],
                       [note_c, "Venues normalizados (TOSEM fusionado; 'Springer' no es una revista)."])
    sheets["sheet5.xml"] = (sd, [60, 12])
    charts["chart5.xml"] = ("MQ4_Journals", 4, list(vtop.index), [int(v) for v in vtop.values])

    # MQ5 — año
    yrs = list(range(2014, 2027))
    yc = C.year.astype(float).astype(int).value_counts()
    rows = [[y, int(yc.get(y, 0))] for y in yrs]
    sd = mq_sheet_data("MQ5: Distribución de artículos por año de publicación", ["Year", "# Papers"], rows,
                       [note_c, "2026: año parcial (búsqueda en curso de año)."], total=True)
    sheets["sheet6.xml"] = (sd, [14, 12])
    charts["chart6.xml"] = ("MQ5_Year", 4, yrs, [r[1] for r in rows])

    # MQ6 — países (≥3 estudios); el mapa lee las celdas vía nombres definidos
    cn, _ = counts(C, "paises")
    ctop = cn[cn >= 3]
    sd = mq_sheet_data("MQ6: Países más frecuentes (≥ 3 estudios, multi-país separado)", ["Country", "# Papers"],
                       [[k, int(v)] for k, v in ctop.items()],
                       [note_c, "País de afiliación de cualquier autor; un estudio cuenta una vez por país."])
    sheets["sheet7.xml"] = (sd, [28, 12])
    n_ctry = len(ctop)

    # MQ7, MQ9, MQ11, MQ12 — total + desglose por tarea; MQ10 pastel por técnica
    for sheet, chart, sh, col, title, hdr in [
        ("sheet8.xml", "chart7.xml", "MQ7_Datasets", "datasets", "MQ7: Familias de datasets más comunes", "Dataset family"),
        ("sheet10.xml", "chart9.xml", "MQ9_EvalMetrics", "metricas", "MQ9: Grupos de métricas de evaluación", "Metric group"),
        ("sheet12.xml", "chart11.xml", "MQ11_MLModels", "modelos", "MQ11: Familias de modelos de ML más comunes", "Model family"),
        ("sheet13.xml", "chart12.xml", "MQ12_BioInspired", "bio", "MQ12: Algoritmos bio-inspirados más comunes", "Bio-inspired algorithm"),
    ]:
        rows = by_task(C, col)
        notes = [note_c + " Columnas por tarea: n de estudios de esa tarea.",
                 f"Estudios sin dato: {int((C[col] == '').sum())}."]
        extra = []
        if col == "bio":
            rol, _ = counts(C[C.bio != ""], "bio_rol")
            notes.append(f"Estudios con algún algoritmo bio-inspirado: {int((C.bio != '').sum())} de {N}.")
            extra = [(0, ["Rol del algoritmo", "# Papers"], [[k, int(v)] for k, v in rol.items()])]
        sd = mq_sheet_data(title, [hdr, "# Papers (Total)"] + task_hdr, rows, notes, extra_blocks=extra)
        sheets[sheet] = (sd, [44, 16] + [18] * len(TASKS))
        charts[chart] = (sh, 4, [r[0] for r in rows], [r[1] for r in rows])

    rows = by_task(C, "hpo_tecnica")
    sd = mq_sheet_data("MQ10: ¿Los estudios reportan una técnica de ajuste de hiperparámetros?",
                       ["Técnica de HPO", "# Papers (Total)"] + task_hdr, rows,
                       [note_c, "Sólo cuenta si el estudio nombra la técnica (grid/random search, bayesiana, "
                                "metaheurística, AutoML). La marca original 'Sí/No' se descartó."], total=True)
    sheets["sheet11.xml"] = (sd, [36, 16] + [18] * len(TASKS))
    charts["chart10.xml"] = ("MQ10_HyperparamTuning", 4, [r[0] for r in rows], [r[1] for r in rows])

    # MQ8 (reformulada) — modelos en estudios de salida continua (B)
    rows = []
    tot_b, ex_b = counts(B, "modelos")
    tot_cl, _ = counts(C[C.tg == "CLASS"], "modelos")
    for k, v in tot_b.items():
        rows.append([k, int(v), int(tot_cl.get(k, 0))])
    sd = mq_sheet_data("MQ8 (reformulada): modelos en estudios de salida continua (densidad + recuento)",
                       ["Model family", f"# Papers continuous (B, n={len(B)})",
                        f"# Papers classification (C, n={int((C.tg == 'CLASS').sum())})"], rows,
                       ["La regresión logística es clasificación: ya no se cuenta como 'tipo de regresión' (R9).",
                        "B = 28 estudios de densidad + 72 de recuento (5 de la búsqueda, 67 por snowballing)."])
    sheets["sheet9.xml"] = (sd, [36, 26, 28])
    charts["chart8.xml"] = ("MQ8_RegressionTypes", 4, [r[0] for r in rows], [r[1] for r in rows])

    # ---- aplicar a las hojas MQ
    for f, (sd, widths) in sheets.items():
        data, _, dim = sd
        files[f"xl/worksheets/{f}"] = replace_sheet(txt(f"xl/worksheets/{f}"), data, dim, widths).encode("utf-8")
    for f, (sh, start, cats, vals) in charts.items():
        x = update_chart(txt(f"xl/charts/{f}"), sh, start, cats, vals)
        if f == "chart8.xml":
            x = set_title(x, "Most used regression algorithms", "Most used models for continuous outcomes (density / count)")
        files[f"xl/charts/{f}"] = x.encode("utf-8")

    # ---- hoja Data (corpus C ∪ B) y tabla
    data_cols = [("ID", "id", 8), ("Paper Name", "title", 60), ("Authors", "autores", 40), ("Countries", "paises", 22),
                 ("Published In", "venue", 34), ("Year", "year", 7), ("Fuente", "fuente", 16), ("Database", "database", 22),
                 ("Tarea", "tarea", 10), ("En corpus C", "en_C", 12), ("En síntesis B", "en_B", 12), ("En síntesis A", "en_A", 12),
                 ("Dataset families", "datasets", 30), ("ML model families", "modelos", 34), ("Metric groups", "metricas", 26),
                 ("HPO technique", "hpo_tecnica", 22), ("Bio-inspired", "bio", 24), ("Bio role", "bio_rol", 22),
                 ("Texto codificado", "texto_codificado", 18), ("DOI", "doi", 30)]
    dd = d.sort_values(["en_C", "id"], ascending=[False, True])
    yesno = {"True": "Sí", "False": "No"}
    rows_xml = ['<row r="1">' + "".join(cell(f"{COLS[i]}1", h, 1) for i, (h, _, _) in enumerate(data_cols)) + "</row>"]
    for r, (_, rec) in enumerate(dd.iterrows(), start=2):
        vals = []
        for h, c, _ in data_cols:
            v = rec[c]
            v = yesno.get(v, v) if c.startswith("en_") else v
            v = int(float(v)) if c == "year" and v else v
            vals.append(cell(f"{COLS[i] if (i := len(vals)) < 26 else 'A'}{r}", v))
        rows_xml.append(f'<row r="{r}">' + "".join(vals) + "</row>")
    last = len(dd) + 1
    ref = f"A1:{COLS[len(data_cols) - 1]}{last}"
    s1 = txt("xl/worksheets/sheet1.xml")
    s1 = replace_sheet(s1, "".join(rows_xml), ref, [w for _, _, w in data_cols])
    files["xl/worksheets/sheet1.xml"] = s1.encode("utf-8")
    t1 = txt("xl/tables/table1.xml")
    tcols = "".join(f'<tableColumn id="{i + 1}" name="{escape(h)}"/>' for i, (h, _, _) in enumerate(data_cols))
    t1 = re.sub(r'ref="A1:[A-Z]+\d+"', f'ref="{ref}"', t1)
    t1 = re.sub(r"<tableColumns.*</tableColumns>", f'<tableColumns count="{len(data_cols)}">{tcols}</tableColumns>', t1, flags=re.S)
    files["xl/tables/table1.xml"] = t1.encode("utf-8")

    # ---- nueva hoja Cribado_busqueda (367 registros de la búsqueda con su decisión)
    cr_cols = [("ID", "id", 8), ("Paper Name", "title", 60), ("Year", "year", 7), ("Database", "database", 24),
               ("Dominio", "dominio", 16), ("Tarea", "tarea", 10), ("Exclusión", "exclusion", 10),
               ("Motivo", "exclusion_motivo", 44), ("Incluido en C", "incluido_C_amplio", 12), ("Duplicado de", "duplicate_of", 12)]
    rows_xml = ['<row r="1">' + "".join(cell(f"{COLS[i]}1", h, 1) for i, (h, _, _) in enumerate(cr_cols)) + "</row>"]
    for r, (_, rec) in enumerate(mm.iterrows(), start=2):
        vals = []
        for i, (h, c, _) in enumerate(cr_cols):
            v = rec[c]
            v = yesno.get(v, v) if c == "incluido_C_amplio" else v
            v = int(float(v)) if c == "year" and v else v
            vals.append(cell(f"{COLS[i]}{r}", v))
        rows_xml.append(f'<row r="{r}">' + "".join(vals) + "</row>")
    widths = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, (_, _, w) in enumerate(cr_cols))
    files["xl/worksheets/sheet14.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<dimension ref="A1:J{len(mm) + 1}"/><sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<sheetFormatPr defaultRowHeight="14.4"/><cols>{widths}</cols><sheetData>{"".join(rows_xml)}</sheetData>'
        f'<autoFilter ref="A1:J{len(mm) + 1}"/>'
        '<pageMargins left="0.75" right="0.75" top="1" bottom="1" header="0.5" footer="0.5"/></worksheet>').encode("utf-8")

    # ---- workbook: hoja nueva, nombres definidos del mapa, sin calcChain, recálculo al abrir
    wb = txt("xl/workbook.xml")
    wb = wb.replace("</sheets>", '<sheet name="Cribado_busqueda" sheetId="14" r:id="rId18"/></sheets>')
    wb = re.sub(r"(MQ6_Countries!\$A\$4:\$A\$)\d+", rf"\g<1>{3 + n_ctry}", wb)
    wb = re.sub(r"(MQ6_Countries!\$B\$4:\$B\$)\d+", rf"\g<1>{3 + n_ctry}", wb)
    wb = re.sub(r'<calcPr calcId="(\d+)"/>', r'<calcPr calcId="\1" fullCalcOnLoad="1"/>', wb)
    wb = re.sub(r'(<sheetView[^>]*?) activeTab="\d+"', r"\1", wb)
    files["xl/workbook.xml"] = wb.encode("utf-8")
    rels = txt("xl/_rels/workbook.xml.rels")
    rels = re.sub(r'<Relationship Id="rId17" Type="[^"]+calcChain" Target="calcChain.xml"/>', "", rels)
    rels = rels.replace("</Relationships>", '<Relationship Id="rId18" Type="http://schemas.openxmlformats.org/'
                        'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet14.xml"/></Relationships>')
    files["xl/_rels/workbook.xml.rels"] = rels.encode("utf-8")
    ct = txt("[Content_Types].xml")
    ct = re.sub(r'<Override PartName="/xl/calcChain.xml"[^>]*/>', "", ct)
    ct = ct.replace("</Types>", '<Override PartName="/xl/worksheets/sheet14.xml" ContentType="application/'
                    'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
    files["[Content_Types].xml"] = ct.encode("utf-8")
    files.pop("xl/calcChain.xml", None)
    app = txt("docProps/app.xml")
    app = app.replace("<vt:i4>13</vt:i4>", "<vt:i4>14</vt:i4>").replace('<vt:vector size="13" baseType="lpstr">', '<vt:vector size="14" baseType="lpstr">')
    app = app.replace("<vt:lpstr>MQ12_BioInspired</vt:lpstr></vt:vector>", "<vt:lpstr>MQ12_BioInspired</vt:lpstr><vt:lpstr>Cribado_busqueda</vt:lpstr></vt:vector>")
    files["docProps/app.xml"] = app.encode("utf-8")
    # sólo una hoja seleccionada al abrir (la Data)
    for f in list(files):
        if f.startswith("xl/worksheets/sheet") and f != "xl/worksheets/sheet1.xml":
            files[f] = files[f].replace(b' tabSelected="1"', b"")

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in zin.namelist():
            if n in files:
                zout.writestr(n, files[n])
        for n in files:
            if n not in zin.namelist():
                zout.writestr(n, files[n])
    print(f"Escrito {OUT.name}: Data {len(dd)} estudios (C={N}, B={len(B)}), Cribado {len(mm)} registros, "
          f"MQ6 países={n_ctry}")


if __name__ == "__main__":
    main()
