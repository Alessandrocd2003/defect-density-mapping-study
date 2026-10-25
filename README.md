# Supplementary material

**A Systematic Mapping and Review Study on Software Defect Density Prediction Models** (INTELÉTICA, revised version)

## Overview
This repository is the replication package of a systematic mapping study on machine learning models for software
defect prediction published between 2014 and 2026, with a focused review of defect density prediction and of the use
of hyperparameter optimization and bio-inspired algorithms. It contains every record and decision behind the results
reported in the paper:
- the search strategy and its validation (precision per database and recall against an independent control set);
- the screening log of the 367 records retrieved from Scopus, IEEE Xplore, ACM Digital Library and SpringerLink;
- the backward and forward snowballing log (1372 candidates screened over three iterations);
- the coded extraction matrix of the 112 primary studies, classified by predictive task, with the evidence behind each code;
- the scripts that regenerate all tables and figures of the paper from these data.

The aim is that every number in the paper can be traced to a record in this repository and reproduced with the code.

Package generated on 2026-10-24. License: CC BY 4.0 for the data (`data/`, see `LICENSE-DATA`) and MIT for the code
(`code/`, see `LICENSE`). How to cite: `CITATION.cff`.

## Contents
| Folder | Content |
|---|---|
| `data/01_search/` | PICOC, search string, database-specific queries, precision per database, control set for recall. |
| `data/02_screening/` | `screening_log.csv`: decision, exclusion code and predictive task for each of the 367 records retrieved by the database search; PRISMA flow. |
| `data/03_snowballing/` | Seeds of the three iterations; `snowball_screening_log.csv` with the decision for each of the 1372 candidates screened; the 85 studies added (18 defect density, 67 defect count); a sample of automatically excluded candidates for false-negative checking. |
| `data/04_extraction/` | `extraction_matrix_coded.csv` (179 studies of corpora B and C, with coded categories, coding evidence and the original free-text extraction fields); the original extraction form; codebook; coding rules; quality instrument. |
| `data/05_results/` | Tables per mapping question (CSV), figures (as in the paper, and broken down by task), and the MQ analysis workbook (Excel). |
| `data/06_references/` | Audit of every cited reference against Crossref and the corrections applied. |
| `code/` | Scripts and their manual inputs to reproduce the corpus, coding, tables and figures (`python run_all.py`; see `requirements.txt`). |

## Key numbers
- Records identified: 367 (Scopus 37, IEEE Xplore 39, ACM DL 111, SpringerLink 180); unique: 365.
- Excluded: 149 outside software engineering (E6), 102 software engineering but not about defects (E2), 11 secondary (E7), 4 without a prediction model (E4); 5 pending.
- Eligible from the search: 94. Snowballing (3 iterations) and control set: +18 defect-density studies.
- Mapping corpus C: 112 studies (density 28, classification 49, effort-aware 21, count 5, other 9).

## Notes on reuse
- Abstracts and API responses are not redistributed. `code/run_all.py` re-downloads them from OpenAlex and Crossref using the identifiers in the CSV files.
- The 18 studies added by snowballing and the control set were coded from title and abstract, or from the title alone when no abstract was available (7 studies). Their full-text extraction is pending (`coded_from` column).
- Free-text extraction fields (`form_*`) are the reviewers' original notes, written in Spanish or English.
- Inter-rater agreement was not quantified, and quality was recorded only as the original global score (see the paper, Sections 3 and 7).
