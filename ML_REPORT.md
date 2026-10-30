# Machine learning report

Implemented: character TF-IDF (3–5 grams, 50,000 features), class-balanced logistic regression, fixed random seed, exact duplicate removal, project-disjoint holdout, artifact versioning and dataset checksum. Metrics are computed only after training on supplied data.

Status: no research training run or production checkpoint has been completed. No numerical accuracy or performance claim is made. A model-unavailable response is returned until MODEL_PATH is configured. The static analyzer's risk score is a rule-weighted indicator and is never presented as ML output.

Suggested source: [Microsoft CodeXGLUE defect detection](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection), derived from Devign. The upstream task describes C/C++ vulnerable-function classification. The [CodeXGLUE repository](https://github.com/microsoft/CodeXGLUE) specifies C-UDA for datasets. Review upstream and source-project obligations before redistribution. No dataset is bundled here.

Remaining: near-duplicate detection, independently curated validation, calibrated probability evaluation, CodeBERT fine-tuning/comparison, and reproducibility across pinned research environments. The transformer is deliberately not replaced with fictitious scores or random predictions.
