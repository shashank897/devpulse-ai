# Machine learning report

Current packaged model: **Extra Trees v3.0.0**, promoted on 2026-11-01. See the final section for its comparison with the original logistic-regression baseline and Random Forest. Earlier sections describe historical experiments.

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

These results indicate weak discrimination across the held-out project. The model is a reproducible research baseline, **not a reliable security detector** and should not drive release decisions. Probabilities are uncalibrated; threshold 0.5 was fixed in advance. No threshold or hyperparameter was selected against the test result. There are only two projects, so uncertainty and generalization are substantial. The trained artifact is packaged with the Render image for an explicit experimental inference panel. The dataset itself is not deployed.

The static analyzer's risk score is a rule-weighted indicator and is never presented as ML output.

Suggested source: [Microsoft CodeXGLUE defect detection](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection), derived from Devign. The upstream task describes C/C++ vulnerable-function classification. The [CodeXGLUE repository](https://github.com/microsoft/CodeXGLUE) specifies C-UDA for datasets. Review upstream and source-project obligations before redistribution. No dataset is bundled here.

Remaining: near-duplicate detection, independently curated validation, calibrated probability evaluation, CodeBERT fine-tuning/comparison, and reproducibility across pinned research environments. The transformer is deliberately not replaced with fictitious scores or random predictions.

## Retraining experiment (2026-10-31)

Completed six logistic-regression configurations: character TF-IDF alone or combined with case-sensitive code-token TF-IDF, with regularization C = 0.1, 1 or 10. Settings were selected using 2,471 FFmpeg validation functions from 1,471 commits, disjoint from the 7,195 inner-training functions and 4,410 commits. The selected model was refitted on all 9,666 FFmpeg functions and evaluated once on the same historical 17,497-function QEMU test project.

Validation PR-AUC selected the character model with C = 0.1. Its threshold 0.4804684359 maximized validation balanced accuracy. An initial validation-only threshold trial using F1 was stopped before test evaluation because it classified almost all validation functions as positive. Neither configuration nor threshold was selected using the new QEMU results. The historical baseline QEMU results were already known, so this is a development comparison rather than an independent new benchmark.

| Metric | Deployed baseline | New candidate | Change (percentage points) |
| --- | ---: | ---: | ---: |
| Accuracy | 56.61% | 54.46% | -2.15 |
| Precision | 48.57% | 46.18% | -2.39 |
| Recall | 31.84% | 41.91% | +10.06 |
| F1 | 38.47% | 43.94% | +5.47 |
| ROC-AUC | 0.5481 | 0.5384 | -0.97 |
| PR-AUC (average precision) | 0.4724 | 0.4552 | -1.72 |

**The goal of improving all six quality metrics was not achieved.** The candidate finds more labeled defects but produces more false alarms and has weaker ranking discrimination. Its confusion matrix is TN 6,405, FP 3,640, FN 4,329, TP 3,123. The candidate was not promoted; the deployed baseline remains the active model.

The candidate artifact is saved locally as `artifacts/experiment-v2/candidate.joblib` (2,113,451 bytes). Measured inference took 1.9669 ms/function, approximately 508 functions/second; this is an uncontrolled local timing and does not establish a speed improvement over the earlier run. Scores remain uncalibrated. The API now reads an artifact's threshold metadata, with 0.5 as the legacy default; 18 backend tests passed, including checks for threshold handling and baseline inference.

Reproduce using `python ml/train_improved.py`; the source dataset files must be present. Input parquet checksums, package versions, every validation result and final test metrics are recorded in [ml/experiments/devign-v2.json](ml/experiments/devign-v2.json). See [DATASETS.md](DATASETS.md) for verified dataset sources and downloads. The current dataset is already available locally. PrimeVul is a candidate for broader future training with chronological evaluation; it was not downloaded or used in this experiment. Transformer training has not been performed.

## Two additional models (2026-11-01)

Trained Random Forest and Extra Trees with 160 trees, balanced class weights, character TF-IDF (3–5 grams, 50,000 features), seed 42 and two workers. Both selected depth 16 from depths 16, 32 and 48. Model settings and thresholds were selected on 2,471 FFmpeg validation examples, with commits disjoint from the 7,195 inner-training examples. Selection maximized the worst of six metric differences from an inner-fit logistic-regression reference, with average difference breaking ties. All settings were locked before evaluation on the historical 17,497-example QEMU holdout. Final models used all 9,666 FFmpeg examples.

| Metric | Original logistic regression | Random Forest | Extra Trees (promoted) |
| --- | ---: | ---: | ---: |
| Accuracy | 56.61% | 61.75% | 57.99% |
| Precision | 48.57% | 60.31% | 51.08% |
| Recall | 31.84% | 29.79% | 32.03% |
| F1 | 38.47% | 39.88% | 39.37% |
| ROC-AUC | 0.5481 | 0.5966 | 0.5620 |
| PR-AUC | 0.4724 | 0.5909 | 0.5095 |

Extra Trees improved all six quality point estimates; these small gains have not been shown statistically significant. Random Forest improved five but reduced recall. The historical QEMU results were already known, so this is a development comparison rather than an independent benchmark. Neither model is a reliable security detector; scores remain uncalibrated.

Random Forest: threshold 0.5005950521; confusion matrix [[8584, 1461], [5232, 2220]]; compressed artifact 1,908,518 bytes; local inference 1.9648 ms/function (509.0 functions/second).

Extra Trees: threshold 0.5042610665; confusion matrix [[7759, 2286], [5065, 2387]]; compressed artifact 2,069,797 bytes; local inference 2.1183 ms/function (472.1 functions/second).

Timing is an uncontrolled local batch measurement, not a demonstrated speed improvement. Only the six quality metrics improved together. Extra Trees is packaged at the existing `artifacts/baseline.joblib` path to preserve deployment configuration. Historical baseline evaluation remains unchanged for reproducible comparisons. Both candidate artifacts remain under `artifacts/experiment-v3/`.

Reproduce with `python ml/train_trees.py --output artifacts/new-experiment`. Full dataset checksums, settings, validation results, environment versions and final metrics: [v3 experiment](ml/experiments/devign-v3.json). Saved artifacts passed a prediction round-trip check. Algorithm references: [Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [Extra Trees](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html).
