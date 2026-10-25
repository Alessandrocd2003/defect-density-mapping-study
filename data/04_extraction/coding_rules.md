# Coding rules

Free-text extraction fields (and, for snowballing studies, title and abstract, or the title alone) are coded
with the regular expressions below (case-insensitive). Implemented in `code/revision/F3_analisis/scripts/06_codificar_extraccion.py`.
Each coded value keeps the matched terms in the `evidence_*` columns of `extraction_matrix_coded.csv`.

Additional rules: sentences containing a negation (no, not, without, sin, none…) are ignored for bio-inspired
algorithms and hyperparameter optimization; a metaheuristic counts as an HPO technique only if the text mentions
parameter tuning; for abstracts, accuracy/precision alone do not count as classification metrics (they are often
used generically); the 'mined OSS repositories' family is assigned only when no named benchmark is found.

## Dataset families

| Category | Regular expression |
|---|---|
| PROMISE | `promise\|jureczko\|\bcamel\b\|xalan\|xerces\|\bivy\b\|jedit\|log4j\|\bpoi\b\|synapse\|velocity\|\bant\b` |
| NASA MDP | `nasa\|\bmdp\b\|\b(kc[1-4]\|jm1\|pc[1-5]\|cm1\|mw1\|mc[12])\b` |
| AEEEM / Bug Prediction Dataset | `aeeem\|bug prediction dataset\|d.ambros\|equinox\|mylyn\|\bpde\b\|eclipse jdt` |
| ReLink | `relink\|zxing` |
| SOFTLAB | `softlab\|\bar[1-6]\b` |
| ISBSG | `isbsg` |
| JIT (Kamei et al.) | `kamei\|bugzilla\|columba\|postgresql` |
| Defects4J | `defects4j` |
| Industrial / proprietary | `industr\|propriet\|privad\|company\|empresa\|alibaba\|sap hana\|automotive\|telecom` |
| Mined OSS repositories (GitHub/Jira) | `github\|jira\|apache\|open[- ]source\|\boss\b\|código abierto\|repositor` |

## Model families

| Category | Regular expression |
|---|---|
| Random Forest | `random forest\|bosque aleatorio\|\brf\b` |
| Logistic Regression | `logistic\|logística\|\blr\b` |
| Linear Regression / GLM | `generalized linear\|\bglms?\b\|linear regression\|regresión lineal\|\bmlr\b\|\bols\b\|least squares\|mínimos cuadrados\|\bealr\b` |
| SVM / SVR | `\bsvm\b\|\bsvr\b\|support vector\|vectores de soporte\|\bsmo\b` |
| Naive Bayes | `naive bayes\|naïve bayes\|\bnb\b\|bayes ingenuo` |
| Decision / Regression Tree | `decision tree\|árbol(es)? de decisión\|regression tree\|\bj48\b\|c4\.5\|\bcart\b\|\bm5\b\|\bdtr?\b` |
| k-NN | `\bk-?nn\b\|k-nearest\|nearest neighbo\|vecinos\|\bibk\b\|\bk\*` |
| MLP / ANN / ELM | `\bmlp\b\|perceptr\|neural network\|red(es)? neuronal\|\bann\b\|\brbf\b\|\bgrnn\b\|extreme learning\|\belm\b\|\bdnn\b\|deep neural` |
| CNN | `\bcnn\b\|convolutional\|convolucional` |
| RNN / LSTM | `lstm\|\brnn\b\|recurrent\|recurrente\|\bgru\b` |
| Transformer / LLM | `lenguaje de código\|\bclms?\b\|transformer\|\bbert\|codebert\|\bllm\|\bgpt\|\bt5\b\|language model` |
| Boosting | `boost\|\bgbm\b\|lightgbm\|catboost\|gradient boosting` |
| Ensemble (bagging/stacking/voting) | `bagging\|stacking\|voting\|ensemble\|ensamble` |
| Count models (Poisson/NB/ZIP) | `poisson\|negative binomial\|binomial negativ\|zero-inflated\|hurdle` |
| Learning to Rank | `learning[- ]to[- ]rank\|\bltr\b\|rankboost\|ranking svm\|ranknet` |
| Transfer learning (TCA, BDA…) | `transfer learning\|tca\|bda\|jda` |
| Deep learning (unspecified) | `deep learning\|aprendizaje profundo\|profund` |
| Fuzzy / Grey | `fuzzy\|difus\|grey system\|grey relational` |
| Bayesian network / GP | `bayesian network\|belief network\|red bayesiana\|gaussian process` |
| Unsupervised / clustering | `unsupervised\|no supervisad\|cluster\|k-means` |

## Metric groups

| Category | Regular expression |
|---|---|
| Classification | `true positive\|false positive\|confusion\|accuracy\|exactitud\|precision\|precisión\|recall\|sensitivity\|sensibilidad\|f-?measure\|f1\|f-?score\|\bauc\b\|\broc\b\|\bmcc\b\|g-?mean\|specificity\|especificidad\|kappa\|\bpd\b\|\bpf\b\|balance` |
| Regression error | `\bmae\b\|\bmse\b\|\brmse\b\|r-?squared\|r²\|\br2\b\|coeficiente de determinación\|mmre\|\bmre\b\|pred\s*\(\|\baae\b\|\bare\b\|absolute error\|squared error\|error absoluto\|error cuadrático\|\bsa\b\|standardi[sz]ed accuracy\|residual\|correlation coefficient\|\bfpa\b` |
| Effort-aware | `popt\|pofb\|\bpmi\b\|\bifa\b\|\bpci\b\|@20\|cost[- ]effective\|peffort\|\bacc\b\|ce-score\|aucec` |
| Statistical tests | `p-?value\|wilcoxon\|scott-knott\|friedman\|nemenyi\|cliff\|effect size` |

## HPO technique

| Category | Regular expression |
|---|---|
| Grid search | `grid ?search\|gridsearchcv\|búsqueda en (rejilla\|cuadrícula)\|exhaustive search\|búsqueda exhaustiva` |
| Random search | `random(ized)? search\|búsqueda aleatoria` |
| Bayesian / SMBO | `bayesian optimi[sz]\|optimización bayesiana\|optuna\|hyperopt\|\btpe\b\|\bsmac\b` |
| Metaheuristic / bio-inspired | `bio-?inspir\|genetic\|genétic\|evolutionary\|evolutiv\|particle swarm\|\bpso\b\|firefly\|whale\|grey wolf\|metaheur\|swarm\|enjambre\|cuckoo\|moth\|salp\|\bbaha\b\|nsga\|differential` |
| AutoML / automated tool | `auto-?ml\|auto-sklearn\|tpot\|\bcaret\b\|automated parameter optimi` |

## Bio-inspired algorithms

| Category | Regular expression |
|---|---|
| Genetic Algorithm (GA/NSGA) | `genetic algorithm\|algoritmo genétic\|\bga\b\|nsga\|genético` |
| Genetic Programming | `genetic programming\|programación genética` |
| Differential Evolution | `differential evolution\|evolución diferencial` |
| Particle Swarm Optimization | `particle swarm\|\bpso\b\|enjambre de partículas` |
| Ant / Bee colony | `ant colony\|colonia de hormigas\|\baco\b\|bee colony\|\babc\b` |
| Firefly | `firefly\|luciérnaga\|\bffo\b` |
| Grey Wolf | `gr[ae]y wolf\|lobo gris\|\bgwo\b` |
| Whale (WOA) | `whale\|ballena\|\bwoa\b` |
| Bat | `\bbat\b\|murciélago` |
| Cuckoo search | `cuckoo\|\bcuco\b` |
| Moth-flame | `moth.?flame\|\bmfo\b` |
| Salp swarm | `\bsalp\b` |
| White Shark | `white shark\|tiburón blanco\|\bwso\b` |
| BAHA | `\bbaha\b` |
| Unspecified metaheuristic | `metaheur` |
| Other (butterfly, dolphin, krill…) | `butterfly\|mariposa\|dolphin\|elephant herd\|dragonfly\|krill\|chaotic\|caótic` |

## Role of bio-inspired algorithms

- Feature selection: `feature (subset )?selection|selección de (características|atributos)|feature reduction|reducción de características`
- Hyperparameter tuning: `hyper-?param|hiperpar|tuning|sintoniz|parameter optimi|optimi[sz]\w* (the )?(model )?parameters|ajuste de par|parameter configuration`
- Otherwise: other / undetermined
