# Defect baseline

This is a real trainable scikit-learn TF-IDF + logistic-regression pipeline, not an LLM classifier or a heuristic disguised as ML. No trained model is bundled and no accuracy is claimed.

The project has a preparation helper for the official CodeXGLUE parquet export. Obtain its C-UDA data-use terms and source files from [the dataset card](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection) before training. The downloaded files are intentionally not committed.

```powershell
pip install -r ml/requirements.txt
New-Item -ItemType Directory -Force data | Out-Null
Invoke-WebRequest 'https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/train-00000-of-00001.parquet' -OutFile data/train.parquet
Invoke-WebRequest 'https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/validation-00000-of-00001.parquet' -OutFile data/validation.parquet
Invoke-WebRequest 'https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/test-00000-of-00001.parquet' -OutFile data/test.parquet
python ml/prepare_codexglue.py
python ml/train.py data/devign.jsonl --output artifacts
```

Each prepared JSONL row uses `func`, `target`, and `project`. All three upstream splits are combined before DevPulse creates a project-disjoint FFmpeg-vs-QEMU holdout; exact duplicate code that crosses projects or labels is dropped to prevent leakage. `artifacts/baseline.joblib` and `artifacts/evaluation.json` are generated locally and excluded from Git. This avoids committing research code or model artifacts without review. Do not train on the landing-page fixtures and claim research performance.

The pipeline normalizes whitespace, removes exact duplicates, rejects conflicting duplicate labels, and holds out entire projects with a fixed seed. It reports accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, latency, throughput and model size. Near-duplicate leakage and dataset label noise remain limitations. A future validation split is required for threshold tuning or calibration. The default threshold is fixed at 0.5; probabilities are explicitly uncalibrated.

Set MODEL_PATH to a trusted artifact and install ML dependencies to enable inference. For example in PowerShell: `$env:MODEL_PATH = (Resolve-Path artifacts/baseline.joblib).Path` before starting FastAPI. Joblib deserialization is unsafe for untrusted artifacts; users cannot upload models. This lightweight deployment intentionally excludes PyTorch/CodeBERT fine-tuning. Transformer training and model comparison have not been performed. The local endpoint supports C/C++ only and returns an uncalibrated experimental signal; the hosted preview has no artifact configured.
