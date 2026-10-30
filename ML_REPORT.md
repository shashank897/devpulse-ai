# Machine learning report

Implemented: character TF-IDF (3–5 grams, 50,000 features), class-balanced logistic regression, fixed random seed, exact duplicate removal, project-disjoint holdout, artifact versioning and dataset checksum. Metrics are computed only after training on supplied data.

## Training run (2026-10-30)

Trained locally on the C-UDA CodeXGLUE/Devign parquet dataset (27,318 input functions; official train, validation and test splits combined before a new project-disjoint split). Exact normalized code duplicates with conflicting labels or multiple project assignments were excluded (76 ambiguous duplicate groups; 155 additional duplicate records removed). The seeded group holdout trained on FFmpeg (9,666 examples) and tested on QEMU (17,497 examples). Dataset SHA-256: `8e4f0c64784d38e4c39eb731d11a8e297669c4175d17146f2e507bd56194485c`.

| Metric | Held-out QEMU result |
| --- | ---: |
| Accuracy | 0.5661 |
| Precision | 0.4857 |
| Recall | 0.3184 |
| F1 | 0.3847 |
| ROC-AUC | 0.5481 |
| PR-AUC | 0.4724 |
| Confusion matrix | TN 7,532 · FP 2,513 · FN 5,079 · TP 2,373 |
| Inference throughput | 471.5 functions/second on the training machine |
| Artifact | 2,113,511 bytes |

These results indicate weak discrimination across the held-out project. The model is a reproducible research baseline, **not a reliable security detector** and should not drive release decisions. Probabilities are uncalibrated; threshold 0.5 was fixed in advance. No threshold or hyperparameter was selected against the test result. There are only two projects, so uncertainty and generalization are substantial. The artifact remains local in ignored `artifacts/`; it is not deployed to Render.

The static analyzer's risk score is a rule-weighted indicator and is never presented as ML output.

Suggested source: [Microsoft CodeXGLUE defect detection](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection), derived from Devign. The upstream task describes C/C++ vulnerable-function classification. The [CodeXGLUE repository](https://github.com/microsoft/CodeXGLUE) specifies C-UDA for datasets. Review upstream and source-project obligations before redistribution. No dataset is bundled here.

Remaining: near-duplicate detection, independently curated validation, calibrated probability evaluation, CodeBERT fine-tuning/comparison, and reproducibility across pinned research environments. The transformer is deliberately not replaced with fictitious scores or random predictions.
