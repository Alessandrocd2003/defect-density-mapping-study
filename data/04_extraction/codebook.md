# Codebook

## Identifiers
- `P###`: record retrieved by the database search (P001–P367, in the order of the original extraction form).
- `S###`: study added by snowballing or from the control set (S001–S085).

## Domain (`screening_log.csv`)
| Code | Meaning |
|---|---|
| NO_SE | Outside software engineering (excluded, E6) |
| SE_OTHER | Software engineering, not about software defects (excluded, E2) |
| SE_DEFECT_PRED | Software defect prediction |
| SE_RELIABILITY | Software reliability prediction |

## Predictive task
| Code | Meaning |
|---|---|
| defect_density | Continuous outcome: defects per unit of size |
| defect_count | Number of defects/faults (including ranking by predicted count) |
| defect_proneness_classification | Defective vs. non-defective modules, changes or lines |
| effort_aware_ranking | Modules ranked by predicted defects per unit of inspection effort |
| empirical_statistical_model | Statistical model of defect-related relationships (no ML benchmark) |
| reliability_prediction | Software reliability prediction |
| fault_localization | Localization of faults |
| secondary_study | Review, survey or methodological study (excluded, E7) |

## Corpora
- **C** (`in_map_C`): mapping corpus, 112 studies (94 from the search + 18 defect-density studies from snowballing / control set).
- **A** (`in_density_synthesis_A`): the 28 defect-density studies.
- **B** (`in_continuous_synthesis_B`): continuous outcomes, 100 studies (28 density + 72 count; 67 count studies come from snowballing and are not in C).

## Coded extraction fields (`extraction_matrix_coded.csv`)
Multiple values are separated by `; `. See `coding_rules.md`.
- `dataset_families`, `model_families`, `metric_groups`, `hpo_technique`, `bio_inspired_algorithms`, `bio_inspired_role`
- `evidence_*`: terms that triggered each code (for auditing).
- `form_*`: original free-text extraction fields (reviewers' notes, Spanish/English), available for database-search studies.
- `coded_from`: extraction form / title + abstract / title only. Studies added by snowballing or from the control set are pending full-text extraction.

## Confidence
`high`/`media`/`baja` (high/medium/low): reviewer confidence in the domain or task classification; low-confidence cases
are flagged for verification.
