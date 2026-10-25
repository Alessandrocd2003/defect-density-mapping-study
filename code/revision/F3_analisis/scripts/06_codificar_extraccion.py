"""Fase 3: codificación reproducible de la extracción (datasets, modelos, métricas, HPO, bio-inspirados,
autores, países y venues) para los corpus B y C.

Fuentes de texto:
  - estudios de la búsqueda (P###): campos de la ficha de extracción original
  - estudios de snowballing/control (S###): título + resumen de OpenAlex (provisional hasta la extracción a texto completo)

Cada código guarda los términos que lo activaron (columnas ev_*), para poder auditarlo.
Entradas: F1_corpus/extraction_matrix_v2.xlsx, F2_busqueda/snowballing/*, F3_analisis/metadatos_snowballing.csv
Salida:   F3_analisis/corpus_codificado.csv
Uso:      python revision/F3_analisis/scripts/06_codificar_extraccion.py
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import fulltext  # noqa: E402

REV = Path(__file__).resolve().parents[2]
OUT = REV / "F3_analisis" / "corpus_codificado.csv"

# --- Diccionarios (familia -> regex). Inglés y español porque la ficha original mezcla ambos. ---
DATASETS = {
    "PROMISE": r"promise|jureczko|\bcamel\b|xalan|xerces|\bivy\b|jedit|log4j|\bpoi\b|synapse|velocity|\bant\b",
    "NASA MDP": r"nasa|\bmdp\b|\b(kc[1-4]|jm1|pc[1-5]|cm1|mw1|mc[12])\b",
    "AEEEM / Bug Prediction Dataset": r"aeeem|bug prediction dataset|d.ambros|equinox|mylyn|\bpde\b|eclipse jdt",
    "ReLink": r"relink|zxing",
    "SOFTLAB": r"softlab|\bar[1-6]\b",
    "ISBSG": r"isbsg",
    "JIT (Kamei et al.)": r"kamei|bugzilla|columba|postgresql",
    "Defects4J": r"defects4j",
    "Industrial / proprietary": r"industr|propriet|privad|company|empresa|alibaba|sap hana|automotive|telecom",
    "Mined OSS repositories (GitHub/Jira)": r"github|jira|apache|open[- ]source|\boss\b|código abierto|repositor",
}
MODELS = {
    "Random Forest": r"random forest|bosque aleatorio|\brf\b",
    "Logistic Regression": r"logistic|logística|\blr\b",
    "Linear Regression / GLM": r"generalized linear|\bglms?\b|linear regression|regresión lineal|\bmlr\b|\bols\b|least squares|mínimos cuadrados|\bealr\b",
    "SVM / SVR": r"\bsvm\b|\bsvr\b|support vector|vectores de soporte|\bsmo\b",
    "Naive Bayes": r"naive bayes|naïve bayes|\bnb\b|bayes ingenuo",
    "Decision / Regression Tree": r"decision tree|árbol(es)? de decisión|regression tree|\bj48\b|c4\.5|\bcart\b|\bm5\b|\bdtr?\b",
    "k-NN": r"\bk-?nn\b|k-nearest|nearest neighbo|vecinos|\bibk\b|\bk\*",
    "MLP / ANN / ELM": r"\bmlp\b|perceptr|neural network|red(es)? neuronal|\bann\b|\brbf\b|\bgrnn\b|extreme learning|\belm\b|\bdnn\b|deep neural",
    "CNN": r"\bcnn\b|convolutional|convolucional",
    "RNN / LSTM": r"lstm|\brnn\b|recurrent|recurrente|\bgru\b",
    "Transformer / LLM": r"lenguaje de código|\bclms?\b|transformer|\bbert|codebert|\bllm|\bgpt|\bt5\b|language model",
    "Boosting": r"boost|\bgbm\b|lightgbm|catboost|gradient boosting",
    "Ensemble (bagging/stacking/voting)": r"bagging|stacking|voting|ensemble|ensamble",
    "Count models (Poisson/NB/ZIP)": r"poisson|negative binomial|binomial negativ|zero-inflated|hurdle",
    "Learning to Rank": r"learning[- ]to[- ]rank|\bltr\b|rankboost|ranking svm|ranknet",
    "Transfer learning (TCA, BDA…)": r"transfer learning|tca|bda|jda",
    "Deep learning (unspecified)": r"deep learning|aprendizaje profundo|profund",
    "Fuzzy / Grey": r"fuzzy|difus|grey system|grey relational",
    "Bayesian network / GP": r"bayesian network|belief network|red bayesiana|gaussian process",
    "Unsupervised / clustering": r"unsupervised|no supervisad|cluster|k-means",
}
METRICS = {
    "Classification": r"true positive|false positive|confusion|accuracy|exactitud|precision|precisión|recall|sensitivity|sensibilidad|f-?measure|f1|f-?score|\bauc\b|\broc\b|\bmcc\b|g-?mean|specificity|especificidad|kappa|\bpd\b|\bpf\b|balance",
    "Regression error": r"\bmae\b|\bmse\b|\brmse\b|r-?squared|r²|\br2\b|coeficiente de determinación|mmre|\bmre\b|pred\s*\(|\baae\b|\bare\b|absolute error|squared error|error absoluto|error cuadrático|\bsa\b|standardi[sz]ed accuracy|residual|correlation coefficient|\bfpa\b",
    "Effort-aware": r"popt|pofb|\bpmi\b|\bifa\b|\bpci\b|@20|cost[- ]effective|peffort|\bacc\b|ce-score|aucec",
    "Statistical tests": r"p-?value|wilcoxon|scott-knott|friedman|nemenyi|cliff|effect size",
}
HPO = {  # técnica de optimización de hiperparámetros (sólo cuenta si se menciona la técnica)
    "Grid search": r"grid ?search|gridsearchcv|búsqueda en (rejilla|cuadrícula)|exhaustive search|búsqueda exhaustiva",
    "Random search": r"random(ized)? search|búsqueda aleatoria",
    "Bayesian / SMBO": r"bayesian optimi[sz]|optimización bayesiana|optuna|hyperopt|\btpe\b|\bsmac\b",
    "Metaheuristic / bio-inspired": r"bio-?inspir|genetic|genétic|evolutionary|evolutiv|particle swarm|\bpso\b|firefly|whale|grey wolf|"
                                      r"metaheur|swarm|enjambre|cuckoo|moth|salp|\bbaha\b|nsga|differential",
    "AutoML / automated tool": r"auto-?ml|auto-sklearn|tpot|\bcaret\b|automated parameter optimi",
}
BIO = {
    "Genetic Algorithm (GA/NSGA)": r"genetic algorithm|algoritmo genétic|\bga\b|nsga|genético",
    "Genetic Programming": r"genetic programming|programación genética",
    "Differential Evolution": r"differential evolution|evolución diferencial",
    "Particle Swarm Optimization": r"particle swarm|\bpso\b|enjambre de partículas",
    "Ant / Bee colony": r"ant colony|colonia de hormigas|\baco\b|bee colony|\babc\b",
    "Firefly": r"firefly|luciérnaga|\bffo\b",
    "Grey Wolf": r"gr[ae]y wolf|lobo gris|\bgwo\b",
    "Whale (WOA)": r"whale|ballena|\bwoa\b",
    "Bat": r"\bbat\b|murciélago",
    "Cuckoo search": r"cuckoo|\bcuco\b",
    "Moth-flame": r"moth.?flame|\bmfo\b",
    "Salp swarm": r"\bsalp\b",
    "White Shark": r"white shark|tiburón blanco|\bwso\b",
    "BAHA": r"\bbaha\b",
    "Unspecified metaheuristic": r"metaheur",
    "Other (butterfly, dolphin, krill…)": r"butterfly|mariposa|dolphin|elephant herd|dragonfly|krill|chaotic|caótic",
}
TUNE = re.compile(r"hyper-?param|hiperpar|tuning|sintoniz|parameter optimi|optimi[sz]\w* (the )?(model )?parameters"
                  r"|ajuste de par|parameter configuration", re.I)
FS = re.compile(r"feature (subset )?selection|selección de (características|atributos)|feature reduction"
                r"|reducción de características", re.I)
NEG = re.compile(r"\b(no|not|without|sin|none|ningún|ninguna|n/a|does not|doesn't)\b", re.I)

COUNTRY = {  # nombres en español o variantes -> forma canónica en inglés
    "jordania": "Jordan", "pakistán": "Pakistan", "malasia": "Malaysia", "arabia saudita": "Saudi Arabia",
    "reino unido": "United Kingdom", "uk": "United Kingdom", "italia": "Italy", "noruega": "Norway",
    "republic of korea": "South Korea", "mauricio": "Mauritius", "españa": "Spain",
    "emiratos árabes unidos": "United Arab Emirates", "the netherlands": "Netherlands", "usa": "United States",
    "ee. uu.": "United States", "canadá": "Canada", "alemania": "Germany", "brasil": "Brazil",
}
ISO2 = {"SA": "Saudi Arabia", "AE": "United Arab Emirates", "JO": "Jordan", "MX": "Mexico", "US": "United States",
        "GR": "Greece", "IN": "India", "CN": "China", "HK": "Hong Kong", "CA": "Canada", "AU": "Australia",
        "PK": "Pakistan", "MY": "Malaysia", "KR": "South Korea", "JP": "Japan", "GB": "United Kingdom",
        "DE": "Germany", "BR": "Brazil", "TR": "Turkey", "EG": "Egypt", "IR": "Iran", "SG": "Singapore",
        "TW": "Taiwan", "NZ": "New Zealand", "IT": "Italy", "ES": "Spain", "FR": "France", "SE": "Sweden",
        "FI": "Finland", "NL": "Netherlands", "TN": "Tunisia", "DZ": "Algeria", "MA": "Morocco",
        "ID": "Indonesia", "BD": "Bangladesh", "NG": "Nigeria", "IQ": "Iraq", "LK": "Sri Lanka",
        "KE": "Kenya", "VN": "Vietnam", "TH": "Thailand", "PL": "Poland", "PT": "Portugal", "CH": "Switzerland",
        "IE": "Ireland", "HU": "Hungary", "CZ": "Czech Republic", "RU": "Russia", "ZA": "South Africa",
        "OM": "Oman", "QA": "Qatar", "KW": "Kuwait", "BH": "Bahrain", "LB": "Lebanon", "PS": "Palestine",
        "NO": "Norway", "DK": "Denmark", "BE": "Belgium", "AT": "Austria", "CR": "Costa Rica", "EC": "Ecuador"}

# Venue: patrón -> (nombre canónico, tipo). El primero que coincide gana; si ninguno, se conserva el original.
VENUES = [
    (r"empirical software engineering", ("Empirical Software Engineering", "Revista")),
    (r"transactions on software engineering and methodology|tosem", ("ACM TOSEM", "Revista")),
    (r"ieee transactions on software engineering", ("IEEE TSE", "Revista")),
    (r"ieee transactions on reliability", ("IEEE Transactions on Reliability", "Revista")),
    (r"information and software technology", ("Information and Software Technology", "Revista")),
    (r"journal of systems and software", ("Journal of Systems and Software", "Revista")),
    (r"software quality journal", ("Software Quality Journal", "Revista")),
    (r"automated software engineering", ("Automated Software Engineering", "Revista")),
    (r"journal of software:? evolution and process", ("Journal of Software: Evolution and Process", "Revista")),
    (r"ieee access", ("IEEE Access", "Revista")),
    (r"applied intelligence", ("Applied Intelligence", "Revista")),
    (r"expert systems with applications", ("Expert Systems with Applications", "Revista")),
    (r"knowledge-based systems", ("Knowledge-Based Systems", "Revista")),
    (r"soft computing", ("Soft Computing", "Revista")),
    (r"cluster computing", ("Cluster Computing", "Revista")),
    (r"scientific reports", ("Scientific Reports", "Revista")),
    (r"promise", ("PROMISE", "Congreso")),
    (r"esec/fse|fse.?\d|foundations of software engineering", ("ESEC/FSE", "Congreso")),
    (r"\bicse\b", ("ICSE", "Congreso")),
    (r"\bmsr\b|mining software repositories", ("MSR", "Congreso")),
    (r"\bease\b|evaluation and assessment in software engineering", ("EASE", "Congreso")),
    (r"\besem\b|empirical software engineering and measurement", ("ESEM", "Congreso")),
    (r"\bqrs\b|software quality, reliability and security", ("QRS", "Congreso")),
    (r"springerbriefs|book series|lecture notes|smart innovation", (None, "Capítulo / LNCS")),
    (r"conference|proceedings|symposium|workshop|convention|congress|\bicmss\b|cascon|gecco|saner|profes|"
     r"pakdd|enase|software quality days|internetware|icmla", (None, "Congreso")),
    (r"journal|transactions|letters|review|computing|sciences|programming|tools and applications|informatica|\bai\b",
     (None, "Revista")),
]
VENUE_FIX = {"P158": "ICIRCA 2020 (IEEE)", "P138": "Springer (por confirmar)", "P140": "SpringerBriefs in Computer Science"}


def sentences(text, drop_negated):
    parts = re.split(r"[.;\n]|\s-\s", str(text or ""))
    return " ".join(p for p in parts if not (drop_negated and NEG.search(p)))


def code(text, dic):
    hits = {}
    for fam, rx in dic.items():
        m = sorted({x.group(0).lower() for x in re.finditer(rx, text, re.I)})
        if m:
            hits[fam] = m
    return hits


def norm_venue(v, pid):
    v = VENUE_FIX.get(pid, v).strip()
    for rx, (name, kind) in VENUES:
        if re.search(rx, v, re.I):
            return name or v, kind
    return v, "Otro"


def norm_countries(raw):
    out = set()
    for x in re.split(r"[,;/]| and | y ", raw or ""):
        x = re.sub(r"\(.*?\)", "", x).strip()
        if x:
            out.add(COUNTRY.get(x.lower(), x))
    return sorted(out)


def norm_authors(raw):
    out = []
    for a in re.split(r",| and ", raw or ""):
        a = re.sub(r"^(mr|mrs|ms|dr|prof)\.?\s+", "", a.strip(), flags=re.I).strip(" .")
        if a and len(a) > 2:
            out.append(a)
    return out


def main():
    m = pd.read_excel(REV / "F1_corpus" / "extraction_matrix_v2.xlsx", sheet_name="Corpus_v2",
                      keep_default_na=False, dtype=str)
    m = m[(m["incluido_C_amplio"] == "True") | (m["incluido_B_continuo"] == "True")]
    sb_inc = pd.read_csv(REV / "F2_busqueda" / "snowballing" / "snowball_incluidos.csv", keep_default_na=False, dtype=str)
    cands = pd.concat(pd.read_csv(f, keep_default_na=False, dtype=str)
                      for f in sorted((REV / "F2_busqueda" / "snowballing").glob("snowball_candidatos_it*.csv")))
    abstracts = dict(zip(cands["openalex_id"], cands["resumen"]))
    for f in (REV / "F2_busqueda" / "snowballing" / "raw").glob("it1_seed_C*.json"):  # resúmenes de los controles
        w = json.loads(f.read_text(encoding="utf-8"))["results"][0]
        inv = w.get("abstract_inverted_index") or {}
        abstracts[w["id"]] = " ".join(t for _, t in sorted((p, t) for t, ps in inv.items() for p in ps))
    meta = pd.read_csv(REV / "F3_analisis" / "metadatos_snowballing.csv", keep_default_na=False, dtype=str).set_index("id")
    sb_oa = dict(zip(sb_inc["id"], sb_inc["openalex_id"]))
    ftx = fulltext.load()  # filas completas de la extracción a texto completo (vacío si aún no hay)

    rows = []
    for r in m.itertuples():
        snow = r.fuente != "busqueda_bd"
        from_abstract = False
        if snow and r.id in ftx.index:  # extracción a texto completo: mismos campos que la ficha original
            f = ftx.loc[r.id]
            t_ds = f"{f.datasets_text} {f.conclusions_text}"
            t_ml, t_met = f.ml_text, f.metrics_text
            t_hp = sentences(f"{r.title}. {f.hyper_text} {f.ml_text} {f.design_text}", True)
            t_bio = sentences(f"{f.bio_text} {f.hyper_text} {f.ml_text}", True)
            authors = norm_authors(meta.at[r.id, "authors"])
            countries = sorted({ISO2.get(c.strip(), c.strip()) for c in meta.at[r.id, "countries_iso2"].split(",") if c.strip()})
            venue, vtype = norm_venue(meta.at[r.id, "venue"], r.id)
            source = "ficha de extracción (texto completo)"
        elif snow:
            ab = abstracts.get(sb_oa[r.id], "")
            full = f"{r.title}. {ab}"
            t_ds = t_ml = t_met = t_hp = full
            t_bio = sentences(full, True)
            authors = norm_authors(meta.at[r.id, "authors"])
            countries = sorted({ISO2.get(c.strip(), c.strip()) for c in meta.at[r.id, "countries_iso2"].split(",") if c.strip()})
            venue, vtype = norm_venue(meta.at[r.id, "venue"], r.id)
            source = "título+resumen" if ab else "solo título"
            from_abstract = True
        else:
            t_ds = f"{r.datasets_text} {r.summary_text}"
            t_ml = f"{r.ml_text}"
            t_met = f"{r.metrics_text}"
            t_hp = sentences(f"{r.title}. {r.hyper_text} {r.ml_text} {r.design_text}", True)
            t_bio = sentences(f"{r.bio_text} {r.hyper_text} {r.ml_text}", True)
            authors, countries = norm_authors(r.authors), norm_countries(r.countries)
            venue, vtype = norm_venue(r.venue, r.id)
            source = "ficha de extracción"
        ds, ml, met = code(t_ds, DATASETS), code(t_ml, MODELS), code(t_met, METRICS)
        strict = r"f-?measure|\bf1\b|f-?score|\bauc\b|\broc\b|\bmcc\b|recall|g-?mean|specificity|confusion"
        if from_abstract and "Classification" in met and not re.search(strict, t_met, re.I):
            del met["Classification"]  # en resúmenes "accuracy/precision" suele ser genérico, no la métrica
        oss = "Mined OSS repositories (GitHub/Jira)"
        if oss in ds and len(ds) > 1:  # "repository" junto a un benchmark con nombre no es minería propia
            del ds[oss]
        hp, bio = code(t_hp, HPO), code(t_bio, BIO)
        hpo_meta = "Metaheuristic / bio-inspired"
        if hpo_meta in hp and not TUNE.search(t_hp):  # metaheurística sin mención de ajuste de parámetros: no es HPO
            del hp[hpo_meta]
        bio_txt = f"{t_bio} {t_hp}"
        rol = [k for k, ok in (("Feature selection", FS.search(bio_txt)),
                               ("Hyperparameter tuning", TUNE.search(bio_txt))) if ok] if bio else []
        if bio and not rol:
            rol = ["Other / undetermined"]
        rec = dict(id=r.id, fuente=r.fuente, tarea=r.tarea, year=r.year,
                   en_C=r.incluido_C_amplio == "True", en_B=r.incluido_B_continuo == "True",
                   en_A=r.incluido_A_estricto == "True", texto_codificado=source,
                   venue=venue, venue_tipo=vtype, autores="; ".join(authors), paises="; ".join(countries),
                   datasets="; ".join(ds), modelos="; ".join(ml), metricas="; ".join(met),
                   hpo_tecnica="; ".join(hp) or "Not reported", bio="; ".join(bio), bio_rol="; ".join(rol),
                   ev_datasets=str(ds), ev_modelos=str(ml), ev_metricas=str(met), ev_hpo=str(hp), ev_bio=str(bio),
                   flag_hyper_original=getattr(r, "r_hyperparameters", ""), flag_bio_original=getattr(r, "r_bio_inspired", ""))
        rows.append(rec)
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(len(df), df["texto_codificado"].value_counts().to_dict())
    for c in ("datasets", "modelos", "metricas", "bio"):
        print(c, "vacíos en C:", int((df[df.en_C][c] == "").sum()))


if __name__ == "__main__":
    main()
