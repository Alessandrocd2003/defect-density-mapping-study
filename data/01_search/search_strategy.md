# Search strategy

## PICOC
| Element | Definition | Block |
|---|---|---|
| Population | Software systems or modules for which defect data are recorded | B1 |
| Intervention | ML prediction models, including bio-inspired optimization and hyperparameter tuning | B2 |
| Comparison | No specific comparator required; baseline and competing models are recorded | -- |
| Outcome | Predicted defect density and related outcomes (counts, defect-proneness, effort-aware ranking) and their metrics | B1, B3 |
| Context | Empirical studies using software datasets (open-source, industrial or benchmark) | B3 |

## Search string
```
B1: ("defect density" OR "fault density" OR "bug density" OR "error density" OR "defect frequency" OR "effort-aware defect prediction")
AND
B2: ("bioinspired" OR "bio-inspired" OR "genetic algorithm" OR "evolutionary algorithm" OR "particle swarm optimization" OR "hyper-parameter" OR "hyper-parameters" OR "hyperparameters" OR "hyperparameter" OR "regression")
AND
B3: ("datasets" OR "dataset" OR "evaluation metric" OR "evaluation metrics" OR "software metrics" OR "software metric")
```

## Database-specific queries
| Source | Query / fields | Filters | Hits |
|---|---|---|---|
| Scopus | `TITLE-ABS-KEY(B1 AND B2 AND B3) AND PUBYEAR > 2013` | Years 2014–2026 | 37 |
| IEEE Xplore | Command search, "All Metadata" | Years 2014–2026 | 39 |
| ACM Digital Library | `[Abstract: B1] AND [Abstract: B2] AND [Abstract: B3]` | Publication date 2014–2026 | 111 |
| SpringerLink | Boolean query over full text (field restriction not supported) | Years 2014–2026 | 180 |
| **Total** | | | **367** |

## Validation
- Precision per database: `search_precision_by_database.csv` (25.8% of unique records included).
- Recall against an independent control set of 13 defect-density studies: 6/13 (46%), see `control_set.csv`.
  The search was therefore complemented with backward and forward snowballing (`../03_snowballing/`).
