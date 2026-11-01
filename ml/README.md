# Defect baseline

The deployed classifier uses character TF-IDF and Extra Trees v3.0.0. It is bundled at the legacy path `artifacts/baseline.joblib`; measured results and limitations are in [ML_REPORT.md](../ML_REPORT.md).

The project has a preparation helper for the official CodeXGLUE parquet export. Obtain its C-UDA data-use terms and source files from [the dataset card](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection) before training. The downloaded files are intentionally not committed.

```powershell
pip install -r ml/requirements.txt -r ml/requirements-data.txt
New-Item -ItemType Directory -Force data | Out-Null
Invoke-WebRequest 'https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/train-00000-of-00001.parquet' -OutFile data/train.parquet
Invoke-WebRequest 'https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/validation-00000-of-00001.parquet' -OutFile data/validation.parquet
Invoke-WebRequest 'https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/test-00000-of-00001.parquet' -OutFile data/test.parquet
python ml/prepare_codexglue.py
python ml/train.py data/devign.jsonl --output artifacts/logistic-baseline
```

Each prepared JSONL row uses `func`, `target`, and `project`. All three upstream splits are combined before DevPulse creates a project-disjoint FFmpeg-vs-QEMU holdout; exact duplicate code that crosses projects or labels is dropped to prevent leakage. The reviewed baseline artifact and evaluation are tracked in Git; other generated artifacts and downloaded datasets are ignored. Do not train on the landing-page fixtures and claim research performance.

The baseline normalizes whitespace, removes exact duplicates, rejects conflicting duplicate labels, and holds out entire projects with a fixed seed. It reports accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, latency, throughput and model size. Its threshold is fixed at 0.5; probabilities are uncalibrated. Near-duplicate leakage and dataset label noise remain limitations.

For validation-based model selection, run `python ml/train_improved.py`. This reads the parquet files directly so it can hold out entire FFmpeg commits for validation. It compares six regularization/feature configurations, locks model and threshold selection on validation data, and evaluates the selected model on the original QEMU holdout. It saves a separate candidate without replacing the deployed baseline. See [DATASETS.md](../DATASETS.md) for source links and the experiment protocol.

Run `python ml/train_trees.py` to train Random Forest and Extra Trees using the same character features and project split. Each family tries depths 16, 32 and 48 with 160 trees, balanced class weights and two workers. The model and threshold maximize the worst validation metric difference from a freshly fitted logistic-regression reference, with mean difference breaking ties. Both selections are saved before either final model is evaluated on QEMU. The script saves trusted local artifacts and a comparison under `artifacts/experiment-v3/`; it does not replace the deployed model. Use `--output` with a new directory for another experiment. Historical QEMU results are already known, so subsequent comparisons are development evidence, not independent benchmarks.

Set MODEL_PATH to a trusted artifact and install ML dependencies to enable inference. For example in PowerShell: `$env:MODEL_PATH = (Resolve-Path artifacts/baseline.joblib).Path` before starting FastAPI. Joblib deserialization is unsafe for untrusted artifacts; users cannot upload models. Transformer training has not been performed. The local and hosted endpoints support C/C++ only and return an uncalibrated experimental signal. The updated endpoint reads the artifact's threshold metadata, falling back to 0.5 for legacy models. The deployed Extra Trees threshold is 0.5042610664824371. Historical logistic-regression metrics stay in `artifacts/evaluation.json`; current results are in `ml/experiments/devign-v3.json`. The v2 candidate is saved separately and was not promoted because four quality metrics regressed; see the report.

The reviewed v3 Extra Trees artifact was promoted after all six quality point estimates improved. Random Forest improved five metrics but reduced recall. The v3 gains are not evidence of statistical significance; broader independent evaluation remains necessary. The original deployed logistic-regression artifact can be recovered from Git commit `115fd07`.
