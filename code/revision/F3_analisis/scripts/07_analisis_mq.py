"""Fase 3: MQ1–MQ12 recalculadas sobre el corpus definitivo, con denominadores explícitos y
estratificadas por tipo de tarea. Genera figuras (PNG 300 dpi + PDF), tablas (CSV + LaTeX) y un resumen.

Corpus: C (mapeo, n = 112) para MQ1–MQ12; A (densidad, n = 28) y B (salida continua, n = 100) para las síntesis.
Entradas: F3_analisis/corpus_codificado.csv, F1_corpus/extraction_matrix_v2.xlsx, F2_busqueda/snowballing/*
Salidas:  F3_analisis/figuras/, F3_analisis/tablas/, F3_analisis/resultados_mq.md
Uso:      python revision/F3_analisis/scripts/07_analisis_mq.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REV = Path(__file__).resolve().parents[2]
F3 = REV / "F3_analisis"
FIG, TAB = F3 / "figuras" / "por_tarea", F3 / "tablas"
PARTIAL_YEAR = 2026  # año en curso: se marca como parcial (D1)

# Paleta validada (dataviz, orden fijo; validate_palette.js: PASS, contraste compensado con leyenda y tablas)
TASK_GROUPS = {"DENS": "Defect density", "COUNT": "Defect count", "CLASS": "Classification",
               "EFFORT": "Effort-aware", "OTHER": "Other"}
TASK_COLORS = {"DENS": "#2a78d6", "COUNT": "#eb6834", "CLASS": "#1baf7a", "EFFORT": "#eda100", "OTHER": "#e87ba4"}
SINGLE = "#2a78d6"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100})


def md(obj):
    """Tabla markdown sin dependencias externas."""
    df = obj.to_frame() if isinstance(obj, pd.Series) else obj
    head = "| " + " | ".join([str(df.index.name or "")] + [str(c) for c in df.columns]) + " |"
    sep = "|" + "---|" * (len(df.columns) + 1)
    rows = ["| " + " | ".join([str(i)] + [str(v) for v in r]) + " |" for i, r in zip(df.index, df.values)]
    return "\n".join([head, sep, *rows])


def group(t):
    return t if t in TASK_GROUPS else "OTHER"


def explode(df, col):
    s = df[["id", "tg", col]].copy()
    s[col] = s[col].str.split("; ")
    s = s.explode(col)
    return s[s[col].astype(bool)]


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def table_out(df, name, caption, n_note):
    df.to_csv(TAB / f"{name}.csv", encoding="utf-8-sig")
    tex = df.to_latex(escape=True, caption=f"{caption} {n_note}", label=f"tab:{name}", position="!htbp")
    (TAB / f"{name}.tex").write_text(tex, encoding="utf-8")


def stacked_barh(counts, title, name, total_n, top=None, xlabel="Number of studies"):
    """counts: DataFrame index=categoría, columns=grupos de tarea. Barras horizontales apiladas por tarea."""
    counts = counts.reindex(columns=[g for g in TASK_GROUPS if g in counts.columns]).fillna(0)
    counts["_t"] = counts.sum(axis=1)
    counts = counts.sort_values("_t", ascending=True)
    if top:
        counts = counts.tail(top)
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(counts) + 1.2))
    left = pd.Series(0.0, index=counts.index)
    for g in [c for c in counts.columns if c != "_t"]:
        ax.barh(counts.index, counts[g], left=left, color=TASK_COLORS[g], height=0.62,
                edgecolor="white", linewidth=1.5, label=TASK_GROUPS[g])
        left += counts[g]
    for y, v in zip(counts.index, counts["_t"]):
        ax.text(v + 0.3, y, f"{int(v)}", va="center", fontsize=8, color=INK)
    ax.set_xlabel(f"{xlabel} (N = {total_n})")
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, ncol=5, loc="lower center", bbox_to_anchor=(0.5, -0.32 if len(counts) > 6 else -0.5))
    save(fig, name)


def simple_barh(series, title, name, total_n, xlabel="Number of studies"):
    s = series.sort_values()
    fig, ax = plt.subplots(figsize=(6.4, 0.3 * len(s) + 0.9))
    ax.barh(s.index, s.values, color=SINGLE, height=0.62)
    for y, v in zip(s.index, s.values):
        ax.text(v + 0.1, y, str(int(v)), va="center", fontsize=8, color=INK)
    ax.set_xlabel(f"{xlabel} (N = {total_n})")
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    save(fig, name)


def by_task_table(ex, col, N_task, N):
    """Tabla categoría × tarea en n y % sobre el N de cada tarea (denominadores explícitos)."""
    ct = pd.crosstab(ex[col], ex["tg"]).reindex(columns=[g for g in TASK_GROUPS if g in ex["tg"].unique()]).fillna(0)
    ct["Total"] = ex.drop_duplicates(["id", col]).groupby(col)["id"].nunique()
    ct = ct.sort_values("Total", ascending=False)
    fmt = ct.copy().astype(object)
    for g in ct.columns:
        d = N if g == "Total" else N_task[g]
        fmt[g] = [f"{int(v)} ({100 * v / d:.0f}%)" for v in ct[g]]
    fmt.columns = [f"{TASK_GROUPS.get(g, g)} (n={N if g == 'Total' else N_task[g]})" for g in ct.columns]
    return ct, fmt


def prisma_flow(m_all, crib, C, B):
    """Cifras del diagrama PRISMA calculadas desde la matriz (nada escrito a mano)."""
    s = m_all[m_all.fuente == "busqueda_bd"]
    ex = lambda code: int((s.exclusion == code).sum())
    db = s.groupby("database").size()
    sb = m_all[m_all.fuente != "busqueda_bd"]
    tg = C["tg"].value_counts()
    return dict(
        scopus=int(db.get("Scopus", 0)), ieee=int(db.get("IEEE/IET Electronic Library", 0)),
        acm=int(db.get("ACM Digital Library", 0)), springer=int(db.get("SpringerLink", 0)), identified=len(s),
        dup=ex("DUP"), screened=len(s) - ex("DUP"), e6=ex("E6"), e2=ex("E2"),
        in_domain=len(s) - ex("DUP") - ex("E6") - ex("E2"), e7=ex("E7"), pend=ex("PEND"), e1=ex("E1"),
        e345=ex("E3") + ex("E4") + ex("E5"), eligible=int((s.exclusion == "").sum()), sb_cribados=len(crib),
        control=int((sb.fuente == "conjunto_control").sum()), sb_ft_excl=int((sb.exclusion != "").sum()),
        added_C=int((C.fuente != "busqueda_bd").sum()), b_only=int((~B.id.isin(C.id)).sum()), N=len(C),
        dens=int(tg.get("DENS", 0)), clas=int(tg.get("CLASS", 0)), eff=int(tg.get("EFFORT", 0)),
        other=len(C) - int(tg.get("DENS", 0)) - int(tg.get("CLASS", 0)) - int(tg.get("EFFORT", 0)))


def prisma_figure(f):
    boxes = [
        ("Records identified\n"
         f"Scopus {f['scopus']} · IEEE {f['ieee']} · ACM {f['acm']} · Springer {f['springer']}\n"
         f"(n = {f['identified']})", 0.82),
        (f"Records screened (duplicates removed: {f['dup']})\n(n = {f['screened']})", 0.64),
        (f"Records in domain\n(n = {f['in_domain']})", 0.46),
        (f"Eligible primary studies\n(n = {f['eligible']})", 0.28),
        (f"Studies included in the mapping (C)\n(n = {f['N']})\nDefect density: {f['dens']} · Classification: "
         f"{f['clas']} · Effort-aware: {f['eff']} · Other: {f['other']}", 0.08),
    ]
    second = [f"E7 secondary: {f['e7']}"] + ([f"pending: {f['pend']}"] if f["pend"] else [])
    third = [t for t, n in ((f"E1 not accessible: {f['e1']}", f["e1"]),
                            (f"E3–E5 no data/model/metrics: {f['e345']}", f["e345"])) if n]
    excl = [
        (0.64, f"Excluded (n = {f['e6'] + f['e2']})\nE6 non-software: {f['e6']}\nE2 software, not defects: {f['e2']}"),
        (0.46, f"Excluded{' / pending' if f['pend'] else ''} (n = {f['in_domain'] - f['eligible']})\n"
         + " · ".join(second) + ("\n" + " · ".join(third) if third else "")),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    ax.set_axis_off()
    for text, y in boxes:
        ax.text(0.33, y, text, ha="center", va="center", fontsize=8, color=INK,
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=INK2, lw=0.8))
    for (_, y0), (_, y1) in zip(boxes[:-1], boxes[1:]):
        ax.annotate("", xy=(0.33, y1 + 0.06), xytext=(0.33, y0 - 0.06),
                    arrowprops=dict(arrowstyle="->", color=INK2, lw=0.8))
    for y, text in excl:
        ax.text(0.80, y - 0.09, text, ha="center", va="center", fontsize=7.5, color=INK2,
                bbox=dict(boxstyle="round,pad=0.4", fc="#f4f3f0", ec=GRID, lw=0.8))
        ax.annotate("", xy=(0.62, y - 0.09), xytext=(0.33, y - 0.09), arrowprops=dict(arrowstyle="->", color=GRID, lw=0.8))
    ft = f"\n(excluded at full text: {f['sb_ft_excl']})" if f["sb_ft_excl"] else ""
    ax.text(0.80, 0.22, f"Snowballing (3 iterations, {f['sb_cribados']:,} screened)\n"
                         f"+ control set not retrieved ({f['control']})\n→ +{f['added_C']} defect-density studies{ft}\n"
                         f"(+{f['b_only']} defect-count studies → synthesis B only)",
            ha="center", va="center", fontsize=7.5, color=INK,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=SINGLE, lw=0.9))
    ax.annotate("", xy=(0.60, 0.13), xytext=(0.80, 0.155), arrowprops=dict(arrowstyle="->", color=SINGLE, lw=0.9))
    save(fig, "mq02_prisma")
    # versión JPG para el manuscrito (mismo nombre que usa iberamia.tex)
    for dest in (F3 / "figuras" / "estilo_excel", REV.parent / "Review_Systematic" / "images"):
        if dest.exists():
            fig2 = plt.imread(FIG / "mq02_prisma.png")
            plt.imsave(dest / "mq02_prisma.jpg", fig2[..., :3], format="jpg", pil_kwargs={"quality": 90})


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(exist_ok=True)
    d = pd.read_csv(F3 / "corpus_codificado.csv", keep_default_na=False, dtype=str)
    d["tg"] = d["tarea"].map(group)
    d["year"] = pd.to_numeric(d["year"], errors="coerce")
    C = d[d["en_C"] == "True"].copy()
    A = d[d["en_A"] == "True"].copy()
    B = d[d["en_B"] == "True"].copy()
    N = len(C)
    N_task = C["tg"].value_counts().to_dict()
    out = [f"# Resultados MQ (generado por 07_analisis_mq.py)\n",
           f"Corpus C = {N} · por tarea: " + ", ".join(f"{TASK_GROUPS[g]} {N_task.get(g, 0)}" for g in TASK_GROUPS),
           f"Corpus A (densidad) = {len(A)} · Corpus B (salida continua) = {len(B)}",
           f"Texto codificado en C: {C['texto_codificado'].value_counts().to_dict()}\n"]

    # MQ1 — fuentes
    m_all = pd.read_excel(REV / "F1_corpus" / "extraction_matrix_v2.xlsx", sheet_name="Corpus_v2", keep_default_na=False, dtype=str)
    m = m_all[m_all["exclusion"] != "DUP"]
    mq1 = pd.DataFrame({"Retrieved (unique)": m[m.fuente == "busqueda_bd"].groupby("database").size(),
                        "Included in C": m[m.incluido_C_amplio == "True"].groupby("database").size()}).fillna(0).astype(int)
    mq1 = mq1.rename(index={"Conjunto de control": "Control set (not retrieved)", "IEEE/IET Electronic Library": "IEEE Xplore"})
    mq1["Precision (%)"] = [f"{100 * i / r:.1f}" if r else "n/a" for i, r in zip(mq1["Included in C"], mq1["Retrieved (unique)"])]
    table_out(mq1, "mq01_fuentes", "Records retrieved and studies included per source.", f"(C: N = {N})")
    out += ["## MQ1 Fuentes", md(mq1), ""]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    srcs = mq1.sort_values("Retrieved (unique)").index
    y = range(len(srcs))
    ax.barh([i + 0.18 for i in y], mq1.loc[srcs, "Retrieved (unique)"], height=0.34, color="#a9c8ef", label="Retrieved (unique)")
    ax.barh([i - 0.18 for i in y], mq1.loc[srcs, "Included in C"], height=0.34, color=SINGLE, label="Included in C")
    for i, s in enumerate(srcs):
        ax.text(mq1.at[s, "Retrieved (unique)"] + 1, i + 0.18, str(mq1.at[s, "Retrieved (unique)"]) if mq1.at[s, "Retrieved (unique)"] else "–", va="center", fontsize=8)
        ax.text(mq1.at[s, "Included in C"] + 1, i - 0.18, str(mq1.at[s, "Included in C"]), va="center", fontsize=8)
    ax.set_yticks(list(y), srcs)
    ax.set_xlabel("Number of records / studies")
    ax.set_title("MQ1. Records per source and studies included", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    save(fig, "mq01_fuentes")

    # MQ2 — PRISMA
    crib = pd.concat(pd.read_csv(f, keep_default_na=False, dtype=str)
                     for f in sorted((REV / "F2_busqueda" / "snowballing").glob("snowball_cribado_it*.csv")))
    prisma_figure(prisma_flow(m_all, crib, C, B))
    out += ["## MQ2 Flujo PRISMA", "Ver figuras/mq02_prisma.png y F1_corpus/prisma_resumen.md", ""]

    # MQ3 — autores (frecuencia de autoría, no de citación)
    au = explode(C, "autores")
    top_au = au.groupby("autores")["id"].nunique().sort_values(ascending=False)
    n_auth = len(top_au)
    top = top_au[top_au >= 3]
    table_out(top.to_frame("Studies"), "mq03_autores", "Most frequent authors (>= 3 studies).",
              f"(C: N = {N}; {n_auth} distinct authors)")
    simple_barh(top.head(15), "MQ3. Most frequent authors (≥ 3 studies)", "mq03_autores", N)
    out += ["## MQ3 Autores", f"Autores distintos: {n_auth}. Con ≥3 estudios: {len(top)}", md(top.head(15)), ""]

    # MQ4 — venues
    vt = C.groupby("venue_tipo")["id"].nunique()
    vn = C.assign(venue=C["venue"].replace("", "(missing)")).groupby("venue")["id"].nunique().sort_values(ascending=False)
    vtop = vn[vn >= 2]
    table_out(vtop.to_frame("Studies"), "mq04_venues", "Most frequent publication venues (>= 2 studies).", f"(C: N = {N})")
    simple_barh(vtop, "MQ4. Most frequent venues (≥ 2 studies)", "mq04_venues", N)
    out += ["## MQ4 Venues", f"Por tipo: {vt.to_dict()}", md(vtop), ""]

    # MQ5 — año × tarea
    yr = pd.crosstab(C["year"].astype("Int64"), C["tg"])
    table_out(yr, "mq05_anio_tarea", "Studies per year and predictive task.", f"(C: N = {N}; {PARTIAL_YEAR} partial)")
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    bottom = pd.Series(0, index=yr.index)
    for g in [g for g in TASK_GROUPS if g in yr.columns]:
        ax.bar(yr.index.astype(int), yr[g], bottom=bottom, color=TASK_COLORS[g], width=0.62,
               edgecolor="white", linewidth=1.5, label=TASK_GROUPS[g])
        bottom += yr[g]
    for x, v in zip(yr.index.astype(int), bottom):
        ax.text(x, v + 0.2, str(int(v)) + ("*" if x == PARTIAL_YEAR else ""), ha="center", fontsize=8, color=INK)
    ax.set_xticks(yr.index.astype(int))
    ax.set_ylabel(f"Number of studies (N = {N})")
    ax.set_title(f"MQ5. Studies per year and task (*{PARTIAL_YEAR}: partial year)", loc="left", fontsize=10, color=INK)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0, bottom.max() * 1.15)
    ax.legend(frameon=False, fontsize=8, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    save(fig, "mq05_anio_tarea")
    out += ["## MQ5 Año × tarea", md(yr), ""]

    # MQ6 — países (un estudio cuenta una vez por país de afiliación de cualquier autor)
    co = explode(C, "paises")
    cn = co.groupby("paises")["id"].nunique().sort_values(ascending=False)
    ctop = cn[cn >= 3]
    table_out(ctop.to_frame("Studies"), "mq06_paises", "Countries of author affiliations (>= 3 studies).",
              f"(C: N = {N}; a study counts once per country; {int((C.paises == '').sum())} without data)")
    simple_barh(ctop, "MQ6. Countries of author affiliation (≥ 3 studies)", "mq06_paises", N)
    out += ["## MQ6 Países", md(ctop), f"Sin dato de país: {int((C.paises == '').sum())}", ""]

    # MQ7–MQ12 — por tarea
    specs = [("datasets", "mq07_datasets", "MQ7. Dataset families by task"),
             ("modelos", "mq11_modelos", "MQ11. Model families by task"),
             ("metricas", "mq09_metricas", "MQ9. Evaluation-metric groups by task"),
             ("hpo_tecnica", "mq10_hpo", "MQ10. Hyperparameter-optimization technique by task"),
             ("bio", "mq12_bio", "MQ12. Bio-inspired algorithms by task")]
    for col, name, title in specs:
        ex = explode(C, col)
        ct, fmt = by_task_table(ex, col, N_task, N)
        table_out(fmt, name, title.split(". ", 1)[1] + ".",
                  f"Cells: n (% of the studies of each task). (C: N = {N}; studies without data: {int((C[col] == '').sum())})")
        stacked_barh(ct.drop(columns="Total"), title, name, N, top=15)
        out += [f"## {title}", md(fmt), f"Estudios sin dato: {int((C[col] == '').sum())}", ""]

    # MQ8 (reformulada) — modelos usados en tareas de salida continua (B) vs clasificación
    exb = explode(B, "modelos")
    mq8 = pd.DataFrame({"Continuous outcome (B: density + count)": exb.groupby("modelos")["id"].nunique(),
                        "Classification (C)": explode(C[C.tg == "CLASS"], "modelos").groupby("modelos")["id"].nunique()}).fillna(0).astype(int)
    mq8 = mq8.sort_values(mq8.columns[0], ascending=False)
    table_out(mq8, "mq08_modelos_continuo_vs_clasif", "Model families in continuous-outcome versus classification studies.",
              f"(B: N = {len(B)}; classification in C: N = {N_task.get('CLASS', 0)})")
    out += ["## MQ8 (reformulada) Modelos: salida continua vs clasificación", md(mq8), ""]

    # MQ12 — rol del algoritmo bio-inspirado
    rol = explode(C[C.bio != ""], "bio_rol").groupby("bio_rol")["id"].nunique()
    out += ["## MQ12 Rol del algoritmo bio-inspirado", md(rol),
            f"Estudios con algún algoritmo bio-inspirado: {(C.bio != '').sum()} de {N} "
            f"({100 * (C.bio != '').mean():.1f} %)", ""]

    # MQ10 — comparación con la cifra del manuscrito v1
    hpo_yes = (C["hpo_tecnica"] != "Not reported").sum()
    out += [f"**MQ10:** técnica de HPO reportada en {hpo_yes}/{N} ({100 * hpo_yes / N:.1f} %). "
            f"El manuscrito v1 afirmaba 248/327 (76 %) usando la marca 'Incluye hiperparametrización' sobre todo el corpus, "
            f"marca que incluye casos como coeficientes de regresión o pesos de red.", ""]

    # Síntesis A — tabla de estudios de densidad
    syn = A[["id", "year", "venue", "modelos", "datasets", "metricas", "hpo_tecnica", "bio", "texto_codificado"]].sort_values("year")
    syn.to_csv(TAB / "sintesis_A_densidad.csv", index=False, encoding="utf-8-sig")
    (TAB / "sintesis_A_densidad.tex").write_text(
        syn.drop(columns="texto_codificado").to_latex(index=False, escape=True, longtable=True,
                                                      caption=f"Defect-density prediction studies (A: N = {len(A)}).",
                                                      label="tab:density_studies"), encoding="utf-8")
    mA = explode(A, "metricas").groupby("metricas")["id"].nunique()
    out += ["## Síntesis A (densidad)", f"Métricas en estudios de densidad: {mA.to_dict()}",
            f"Estudios de densidad que reportan métricas de clasificación: {int(A.metricas.str.contains('Classification').sum())}/{len(A)}",
            ""]
    # Síntesis B — resumen agregado de salida continua
    mB = explode(B, "metricas").groupby("metricas")["id"].nunique()
    dB = explode(B, "datasets").groupby("datasets")["id"].nunique().sort_values(ascending=False)
    out += ["## Síntesis B (salida continua)", f"Métricas: {mB.to_dict()}", f"Datasets: {dB.head(8).to_dict()}", ""]

    (F3 / "resultados_mq.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
